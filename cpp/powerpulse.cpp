// Static member initialization
ID3D11Device* PowerPulseGUI::g_pd3dDevice = NULL;
ID3D11DeviceContext* PowerPulseGUI::g_pd3dDeviceContext = NULL;
IDXGISwapChain* PowerPulseGUI::g_pSwapChain = NULL;
ID3D11RenderTargetView* PowerPulseGUI::g_mainRenderTargetView = NULL;

bool PowerPulseGUI::CreateDeviceD3D(HWND hWnd) {
    // Setup swap chain
    DXGI_SWAP_CHAIN_DESC sd;
    ZeroMemory(&sd, sizeof(sd));
    sd.BufferCount = 2;
    sd.BufferDesc.Width = 0;
    sd.BufferDesc.Height = 0;
    sd.BufferDesc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    sd.BufferDesc.RefreshRate.Numerator = 60;
    sd.BufferDesc.RefreshRate.Denominator = 1;
    sd.Flags = DXGI_SWAP_CHAIN_FLAG_ALLOW_MODE_SWITCH;
    sd.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
    sd.OutputWindow = hWnd;
    sd.SampleDesc.Count = 1;
    sd.SampleDesc.Quality = 0;
    sd.Windowed = TRUE;
    sd.SwapEffect = DXGI_SWAP_EFFECT_DISCARD;

    UINT createDeviceFlags = 0;
    D3D_FEATURE_LEVEL featureLevel;
    const D3D_FEATURE_LEVEL featureLevelArray[2] = { D3D_FEATURE_LEVEL_11_0, D3D_FEATURE_LEVEL_10_0, };
    if (D3D11CreateDeviceAndSwapChain(NULL, D3D_DRIVER_TYPE_HARDWARE, NULL, createDeviceFlags, featureLevelArray, 2, D3D11_SDK_VERSION, &sd, &g_pSwapChain, &g_pd3dDevice, &featureLevel, &g_pd3dDeviceContext) != S_OK)
        return false;

    CreateRenderTarget();
    return true;
}

void PowerPulseGUI::CleanupDeviceD3D() {
    CleanupRenderTarget();
    if (g_pSwapChain) { g_pSwapChain->Release(); g_pSwapChain = NULL; }
    if (g_pd3dDeviceContext) { g_pd3dDeviceContext->Release(); g_pd3dDeviceContext = NULL; }
    if (g_pd3dDevice) { g_pd3dDevice->Release(); g_pd3dDevice = NULL; }
}

void PowerPulseGUI::CreateRenderTarget() {
    ID3D11Texture2D* pBackBuffer;
    g_pSwapChain->GetBuffer(0, IID_PPV_ARGS(&pBackBuffer));
    g_pd3dDevice->CreateRenderTargetView(pBackBuffer, NULL, &g_mainRenderTargetView);
    pBackBuffer->Release();
}

void PowerPulseGUI::CleanupRenderTarget() {
    if (g_mainRenderTargetView) { g_mainRenderTargetView->Release(); g_mainRenderTargetView = NULL; }
}

// Forward declare message handler from imgui_impl_win32.cpp
extern IMGUI_IMPL_API LRESULT ImGui_ImplWin32_WndProcHandler(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);

LRESULT WINAPI PowerPulseGUI::WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    if (ImGui_ImplWin32_WndProcHandler(hWnd, msg, wParam, lParam))
        return true;

    switch (msg) {
    case WM_SIZE:
        if (g_pd3dDevice != NULL && wParam != SIZE_MINIMIZED) {
            CleanupRenderTarget();
            g_pSwapChain->ResizeBuffers(0, (UINT)LOWORD(lParam), (UINT)HIWORD(lParam), DXGI_FORMAT_UNKNOWN, 0);
            CreateRenderTarget();
        }
        return 0;
    case WM_SYSCOMMAND:
        if ((wParam & 0xfff0) == SC_KEYMENU) // Disable ALT application menu
            return 0;
        break;
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    case WM_USER + 1: // Custom tray message
        if (lParam == WM_LBUTTONUP || lParam == WM_RBUTTONUP) {
            // Show context menu or restore window
            POINT pt;
            GetCursorPos(&pt);
            SetForegroundWindow(hWnd);
            
            if (lParam == WM_RBUTTONUP) {
                // Show context menu
                HMENU hMenu = CreatePopupMenu();
                AppendMenuA(hMenu, MF_STRING, 1, "Open PowerPulse");
                AppendMenuA(hMenu, MF_SEPARATOR, 0, NULL);
                AppendMenuA(hMenu, MF_STRING, 2, "Exit");
                
                TrackPopupMenu(hMenu, TPM_LEFTALIGN | TPM_BOTTOMALIGN, pt.x, pt.y, 0, hWnd, NULL);
                DestroyMenu(hMenu);
            } else {
                // Left click - restore window
                ShowWindow(hWnd, SW_RESTORE);
                SetForegroundWindow(hWnd);
            }
        }
        return 0;
    case WM_COMMAND:
        if (LOWORD(wParam) == 1) {
            ShowWindow(hWnd, SW_RESTORE);
            SetForegroundWindow(hWnd);
        } else if (LOWORD(wParam) == 2) {
            PostMessage(hWnd, WM_CLOSE, 0, 0);
        }
        return 0;
    }
    return DefWindowProc(hWnd, msg, wParam, lParam);
}

// Main application entry point
int main(int argc, char** argv) {
    // Check command line arguments
    bool cliMode = false;
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--cli") == 0 || strcmp(argv[i], "-c") == 0) {
            cliMode = true;
            break;
        }
    }
    
    // Create the battery monitor
    std::shared_ptr<BatteryMonitor> monitor = std::make_shared<BatteryMonitor>();
    
    if (cliMode) {
        // Run in CLI mode
        PowerPulseCLI cli(monitor);
        cli.Run();
    } else {
        // Run in GUI mode
        PowerPulseGUI gui(monitor);
        if (gui.Initialize()) {
            gui.Run();
            gui.Shutdown();
        }
    }
    
    return 0;
}
    }

    void Shutdown() {
        // Remove system tray icon
        NOTIFYICONDATAA nid = { sizeof(nid) };
        nid.hWnd = hwnd;
        nid.uID = 1;
        Shell_NotifyIconA(NIM_DELETE, &nid);

        // Stop monitoring
        monitor->Stop();

        // Cleanup
        ImGui_ImplDX11_Shutdown();
        ImGui_ImplWin32_Shutdown();
        ImGui::DestroyContext();

        CleanupDeviceD3D();
        DestroyWindow(hwnd);
        UnregisterClass(_T("PowerPulse"), GetModuleHandle(NULL));
    }

private:
    std::shared_ptr<BatteryMonitor> monitor;
    bool running;
    HWND hwnd;
    std::chrono::steady_clock::time_point lastUpdateTime;

    // Direct3D state
    static ID3D11Device* g_pd3dDevice;
    static ID3D11DeviceContext* g_pd3dDeviceContext;
    static IDXGISwapChain* g_pSwapChain;
    static ID3D11RenderTargetView* g_mainRenderTargetView;

    // Forward declarations of helper functions
    static bool CreateDeviceD3D(HWND hWnd);
    static void CleanupDeviceD3D();
    static void CreateRenderTarget();
    static void CleanupRenderTarget();
    static LRESULT WINAPI WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);

    void RenderUI() {
        // Set up the main window style
        ImGui::SetNextWindowPos(ImVec2(0, 0));
        ImGui::SetNextWindowSize(ImGui::GetIO().DisplaySize);
        ImGui::PushStyleVar(ImGuiStyleVar_WindowRounding, 0.0f);
        ImGui::PushStyleVar(ImGuiStyleVar_WindowBorderSize, 0.0f);
        ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(0, 0));

        ImGuiWindowFlags window_flags = ImGuiWindowFlags_MenuBar | ImGuiWindowFlags_NoDocking;
        window_flags |= ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoMove;
        window_flags |= ImGuiWindowFlags_NoBringToFrontOnFocus | ImGuiWindowFlags_NoNavFocus;

        ImGui::Begin("PowerPulse", NULL, window_flags);
        ImGui::PopStyleVar(3);

        // Create a docking space
        ImGuiID dockspace_id = ImGui::GetID("PowerPulseDockSpace");
        ImGui::DockSpace(dockspace_id, ImVec2(0.0f, 0.0f), ImGuiDockNodeFlags_None);

        // Menu bar
        if (ImGui::BeginMenuBar()) {
            if (ImGui::BeginMenu("File")) {
                if (ImGui::MenuItem("Exit", "Alt+F4")) running = false;
                ImGui::EndMenu();
            }
            
            if (ImGui::BeginMenu("View")) {
                if (ImGui::MenuItem("Dashboard")) {}
                if (ImGui::MenuItem("History")) {}
                if (ImGui::MenuItem("Statistics")) {}
                if (ImGui::MenuItem("Settings")) {}
                ImGui::EndMenu();
            }
            
            if (ImGui::BeginMenu("Help")) {
                if (ImGui::MenuItem("About")) {}
                ImGui::EndMenu();
            }
            
            ImGui::EndMenuBar();
        }

        // Battery dashboard window
        ImGui::Begin("Battery Dashboard");
        
        BatteryInfo info = monitor->GetCurrentInfo();
        
        // Battery level indicator
        float percentage = info.percentage;
        ImGui::Text("Battery Level: %.1f%%", percentage);
        
        // Draw a battery icon
        float width = ImGui::GetWindowWidth() * 0.8f;
        float height = 40.0f;
        float x = ImGui::GetCursorScreenPos().x;
        float y = ImGui::GetCursorScreenPos().y;
        ImDrawList* draw_list = ImGui::GetWindowDrawList();
        
        // Battery outline
        draw_list->AddRectFilled(
            ImVec2(x, y),
            ImVec2(x + width, y + height),
            IM_COL32(50, 50, 50, 255)
        );
        
        // Battery level
        ImU32 batteryColor;
        if (percentage <= 20.0f) {
            batteryColor = IM_COL32(255, 0, 0, 255); // Red for low
        } else if (percentage <= 50.0f) {
            batteryColor = IM_COL32(255, 165, 0, 255); // Orange for medium
        } else {
            batteryColor = IM_COL32(0, 255, 0, 255); // Green for high
        }
        
        draw_list->AddRectFilled(
            ImVec2(x + 2, y + 2),
            ImVec2(x + 2 + (width - 4) * (percentage / 100.0f), y + height - 2),
            batteryColor
        );
        
        // Battery cap
        draw_list->AddRectFilled(
            ImVec2(x + width, y + height / 4),
            ImVec2(x + width + 10, y + height * 3 / 4),
            IM_COL32(50, 50, 50, 255)
        );
        
        ImGui::Dummy(ImVec2(width + 10, height + 10));
        
        // Battery info section
        ImGui::Text("Status: %s", info.isCharging ? "Charging" : "Discharging");
        
        if (info.timeRemaining > 0) {
            int hours = info.timeRemaining / 3600;
            int minutes = (info.timeRemaining % 3600) / 60;
            ImGui::Text("Time remaining: %dh %dm", hours, minutes);
        } else {
            ImGui::Text("Time remaining: Unknown");
        }
        
        ImGui::Text("Health: %d%%", info.health);
        ImGui::Text("Charge rate: %.1fW %s", std::abs(info.chargeRate), info.chargeRate > 0 ? "(in)" : "(out)");
        
        // Stats at a glance
        ImGui::Separator();
        ImGui::Text("Quick Stats:");
        
        auto stats = monitor->GetStatistics();
        ImGui::Text("Average discharge rate: %.1f%% per hour", stats.averageDischargePct);
        ImGui::Text("Average charge rate: %.1f%% per hour", stats.averageChargePct);
        
        if (stats.averageCycleTime > 0) {
            int hours = stats.averageCycleTime / 3600;
            int minutes = (stats.averageCycleTime % 3600) / 60;
            ImGui::Text("Average cycle time: %dh %dm", hours, minutes);
        } else {
            ImGui::Text("Average cycle time: Unknown");
        }
        
        ImGui::Text("Deepest discharge: %.1f%%", stats.deepestDischarge);
        ImGui::Text("Lowest health recorded: %.1f%%", stats.lowestHealthPercent);
        
        ImGui::End();
        
        // History graph window
        ImGui::Begin("Battery History");
        
        auto history = monitor->GetHistory();
        if (!history.empty()) {
            // Prepare the data for plotting
            std::vector<float> percentages;
            std::vector<float> timestamps;
            
            for (const auto& entry : history) {
                percentages.push_back(entry.second);
                // Convert to hours from the first entry for x-axis
                timestamps.push_back(static_cast<float>(entry.first - history.front().first) / 3600.0f);
            }
            
            // Plot the graph
            if (ImGui::BeginChild("GraphArea", ImVec2(0, 300), false, ImGuiWindowFlags_HorizontalScrollbar)) {
                if (ImPlot::BeginPlot("Battery Level Over Time", ImVec2(-1, -1))) {
                    ImPlot::SetupAxes("Time (hours)", "Battery Level (%)", 
                                       ImPlotAxisFlags_AutoFit, ImPlotAxisFlags_AutoFit);
                    ImPlot::SetupAxisLimits(ImAxis_X1, 0, timestamps.back(), ImGuiCond_Always);
                    ImPlot::SetupAxisLimits(ImAxis_Y1, 0, 100, ImGuiCond_Always);
                    
                    ImPlot::PlotLine("Battery", timestamps.data(), percentages.data(), percentages.size());
                    
                    // Mark charging and discharging events
                    auto chargeEvents = monitor->GetChargeEvents();
                    auto dischargeEvents = monitor->GetDischargeEvents();
                    
                    for (const auto& event : chargeEvents) {
                        float x = static_cast<float>(event.first - history.front().first) / 3600.0f;
                        ImPlot::PlotVLines("Charging Started", &x, 1);
                    }
                    
                    for (const auto& event : dischargeEvents) {
                        float x = static_cast<float>(event.first - history.front().first) / 3600.0f;
                        ImPlot::PlotVLines("Discharging Started", &x, 1);
                    }
                    
                    ImPlot::EndPlot();
                }
                ImGui::EndChild();
            }
            
            // Add time range selector
            static int timeRange = 24; // Default 24 hours
            ImGui::SliderInt("Time Range (hours)", &timeRange, 1, 168);
            
            // Add export button
            if (ImGui::Button("Export Data")) {
                ExportBatteryData();
            }
        } else {
            ImGui::Text("No history data available.");
        }
        
        ImGui::End();
        
        // Notification settings window
        ImGui::Begin("Notifications");
        
        static float criticalThreshold = monitor->GetNotificationManager().GetThreshold(NotificationManager::CRITICAL_LOW);
        static float lowThreshold = monitor->GetNotificationManager().GetThreshold(NotificationManager::LOW);
        static float optimalThreshold = monitor->GetNotificationManager().GetThreshold(NotificationManager::OPTIMAL_CHARGE_REACHED);
        static float fullThreshold = monitor->GetNotificationManager().GetThreshold(NotificationManager::FULLY_CHARGED);
        
        if (ImGui::SliderFloat("Critical Low (%)", &criticalThreshold, 1.0f, 20.0f)) {
            monitor->GetNotificationManager().SetThreshold(NotificationManager::CRITICAL_LOW, criticalThreshold);
        }
        
        if (ImGui::SliderFloat("Low Battery (%)", &lowThreshold, criticalThreshold + 1.0f, 40.0f)) {
            monitor->GetNotificationManager().SetThreshold(NotificationManager::LOW, lowThreshold);
        }
        
        if (ImGui::SliderFloat("Optimal Charge (%)", &optimalThreshold, 50.0f, 90.0f)) {
            monitor->GetNotificationManager().SetThreshold(NotificationManager::OPTIMAL_CHARGE_REACHED, optimalThreshold);
        }
        
        if (ImGui::SliderFloat("Full Charge (%)", &fullThreshold, optimalThreshold + 1.0f, 100.0f)) {
            monitor->GetNotificationManager().SetThreshold(NotificationManager::FULLY_CHARGED, fullThreshold);
        }
        
        ImGui::Separator();
        ImGui::Text("Custom Notification");
        
        static float customThreshold = 75.0f;
        static char customMessage[256] = "Custom battery threshold reached";
        
        ImGui::SliderFloat("Custom Threshold (%)", &customThreshold, 1.0f, 100.0f);
        ImGui::InputText("Message", customMessage, sizeof(customMessage));
        
        if (ImGui::Button("Add Custom Notification")) {
            monitor->GetNotificationManager().AddCustomThreshold(customThreshold, customMessage);
        }
        
        ImGui::End();
        
        // System tray options window
        ImGui::Begin("System Tray Options");
        
        static bool minimizeToTray = true;
        static bool showBatteryInTray = true;
        static bool startWithWindows = false;
        
        ImGui::Checkbox("Minimize to tray", &minimizeToTray);
        ImGui::Checkbox("Show battery percentage in tray icon", &showBatteryInTray);
        ImGui::Checkbox("Start with Windows", &startWithWindows);
        
        ImGui::Separator();
        
        if (ImGui::Button("Apply Changes")) {
            // Save settings
            SaveSettings(minimizeToTray, showBatteryInTray, startWithWindows);
        }
        
        ImGui::End();
        
        ImGui::End(); // Main window
    }

    void ExportBatteryData() {
        // Create a dialog to save the file
        OPENFILENAMEA ofn;
        char szFile[260] = { 0 };
        
        ZeroMemory(&ofn, sizeof(ofn));
        ofn.lStructSize = sizeof(ofn);
        ofn.hwndOwner = hwnd;
        ofn.lpstrFile = szFile;
        ofn.nMaxFile = sizeof(szFile);
        ofn.lpstrFilter = "CSV Files\0*.csv\0All Files\0*.*\0";
        ofn.nFilterIndex = 1;
        ofn.lpstrFileTitle = NULL;
        ofn.nMaxFileTitle = 0;
        ofn.lpstrInitialDir = NULL;
        ofn.Flags = OFN_PATHMUSTEXIST | OFN_OVERWRITEPROMPT;
        
        if (GetSaveFileNameA(&ofn)) {
            // Ensure it has .csv extension
            std::string filename = ofn.lpstrFile;
            if (filename.substr(filename.find_last_of(".") + 1) != "csv") {
                filename += ".csv";
            }
            
            // Get the data
            auto history = monitor->GetHistory();
            
            // Save to file
            std::ofstream file(filename);
            file << "Timestamp,DateTime,BatteryPercentage\n";
            
            for (const auto& entry : history) {
                char buffer[30];
                std::strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", std::localtime(&entry.first));
                file << entry.first << "," << buffer << "," << entry.second << "\n";
            }
            
            file.close();
        }
    }

    void SaveSettings(bool minimizeToTray, bool showBatteryInTray, bool startWithWindows) {
        // In a real application, these would be saved to the registry or a config file
        // Here we'll just print them for demonstration
        std::cout << "Settings updated:" << std::endl;
        std::cout << "  Minimize to tray: " << (minimizeToTray ? "Yes" : "No") << std::endl;
        std::cout << "  Show battery in tray: " << (showBatteryInTray ? "Yes" : "No") << std::endl;
        std::cout << "  Start with Windows: " << (startWithWindows ? "Yes" : "No") << std::endl;
        
        // For Windows startup, we would add or remove a registry key
        HKEY hKey;
        if (RegOpenKeyExA(HKEY_CURRENT_USER, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", 0, KEY_SET_VALUE, &hKey) == ERROR_SUCCESS) {
            if (startWithWindows) {
                char path[MAX_PATH];
                GetModuleFileNameA(NULL, path, MAX_PATH);
                RegSetValueExA(hKey, "PowerPulse", 0, REG_SZ, (BYTE*)path, strlen(path) + 1);
            } else {
                RegDeleteValueA(hKey, "PowerPulse");
            }
            RegCloseKey(hKey);
        }
    }
};// PowerPulse - Cross-platform Battery Monitoring Application
// A lightweight battery monitoring tool for Windows with CLI and GUI features

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <chrono>
#include <thread>
#include <memory>
#include <mutex>
#include <ctime>
#include <algorithm>
#include <functional>
#include <map>

// Platform-specific headers
#ifdef _WIN32
#include <windows.h>
#include <powrprof.h>
#pragma comment(lib, "PowrProf.lib")
#endif

// GUI library - using Dear ImGui + backends
#include "imgui.h"
#include "imgui_impl_win32.h"
#include "imgui_impl_dx11.h"
#include <d3d11.h>
#include <tchar.h>

// SQLite for storage
#include "sqlite3.h"

// App version
#define APP_VERSION "1.0.0"

// Forward declarations
void SaveBatteryData(const std::string& filename, const std::vector<std::pair<time_t, float>>& batteryData);
std::vector<std::pair<time_t, float>> LoadBatteryData(const std::string& filename);

struct BatteryInfo {
    float percentage;
    bool isCharging;
    long timeRemaining; // in seconds, -1 if unknown
    int health; // percentage of original capacity
    float chargeRate; // in W, positive when charging, negative when discharging
};

class NotificationManager {
public:
    enum NotificationType {
        CRITICAL_LOW = 0,
        LOW,
        OPTIMAL_CHARGE_REACHED,
        FULLY_CHARGED,
        CUSTOM
    };

    NotificationManager() {
        // Initialize notification thresholds
        thresholds[CRITICAL_LOW] = 10.0f;
        thresholds[LOW] = 20.0f;
        thresholds[OPTIMAL_CHARGE_REACHED] = 80.0f;
        thresholds[FULLY_CHARGED] = 100.0f;
    }

    void SetThreshold(NotificationType type, float value) {
        thresholds[type] = value;
    }

    float GetThreshold(NotificationType type) const {
        auto it = thresholds.find(type);
        if (it != thresholds.end()) {
            return it->second;
        }
        return 0.0f;
    }

    void AddCustomThreshold(float value, const std::string& message) {
        customThresholds[value] = message;
    }

    void RemoveCustomThreshold(float value) {
        customThresholds.erase(value);
    }

    void CheckNotifications(float batteryPercentage, bool wasCharging, bool isCharging) {
        // Check built-in thresholds
        for (const auto& threshold : thresholds) {
            if (ShouldNotify(batteryPercentage, threshold.first, wasCharging, isCharging)) {
                SendNotification(GetNotificationMessage(threshold.first, batteryPercentage));
            }
        }

        // Check custom thresholds
        for (const auto& threshold : customThresholds) {
            if (std::abs(batteryPercentage - threshold.first) < 0.5f) {
                if (lastNotifiedCustom.find(threshold.first) == lastNotifiedCustom.end()) {
                    SendNotification(threshold.second);
                    lastNotifiedCustom.insert(threshold.first);
                }
            } else {
                lastNotifiedCustom.erase(threshold.first);
            }
        }
    }

    void ResetNotifications() {
        lastNotified.clear();
        lastNotifiedCustom.clear();
    }

private:
    std::map<NotificationType, float> thresholds;
    std::map<float, std::string> customThresholds;
    std::map<NotificationType, bool> lastNotified;
    std::set<float> lastNotifiedCustom;

    bool ShouldNotify(float batteryPercentage, NotificationType type, bool wasCharging, bool isCharging) {
        auto it = thresholds.find(type);
        if (it == thresholds.end()) return false;

        float threshold = it->second;
        bool shouldNotify = false;

        switch (type) {
        case CRITICAL_LOW:
            shouldNotify = batteryPercentage <= threshold && !isCharging;
            break;
        case LOW:
            shouldNotify = batteryPercentage <= threshold && !isCharging;
            break;
        case OPTIMAL_CHARGE_REACHED:
            shouldNotify = batteryPercentage >= threshold && isCharging && batteryPercentage < thresholds[FULLY_CHARGED];
            break;
        case FULLY_CHARGED:
            shouldNotify = batteryPercentage >= threshold && isCharging;
            break;
        default:
            return false;
        }

        if (shouldNotify && lastNotified[type] == false) {
            lastNotified[type] = true;
            return true;
        } else if (!shouldNotify) {
            lastNotified[type] = false;
        }

        return false;
    }

    std::string GetNotificationMessage(NotificationType type, float batteryPercentage) {
        std::string message;
        switch (type) {
        case CRITICAL_LOW:
            message = "CRITICAL: Battery at " + std::to_string(static_cast<int>(batteryPercentage)) + "%. Please connect to power source immediately!";
            break;
        case LOW:
            message = "Low Battery: " + std::to_string(static_cast<int>(batteryPercentage)) + "%. Consider connecting to a power source.";
            break;
        case OPTIMAL_CHARGE_REACHED:
            message = "Optimal Charge Reached: " + std::to_string(static_cast<int>(batteryPercentage)) + "%. You may disconnect from power source.";
            break;
        case FULLY_CHARGED:
            message = "Battery Fully Charged: " + std::to_string(static_cast<int>(batteryPercentage)) + "%.";
            break;
        default:
            message = "Battery at " + std::to_string(static_cast<int>(batteryPercentage)) + "%.";
        }
        return message;
    }

    void SendNotification(const std::string& message) {
#ifdef _WIN32
        // Windows notification
        NOTIFYICONDATAA nid = { sizeof(nid) };
        nid.uFlags = NIF_INFO;
        strcpy_s(nid.szInfo, message.c_str());
        strcpy_s(nid.szInfoTitle, "PowerPulse");
        nid.dwInfoFlags = NIIF_INFO;
        Shell_NotifyIconA(NIM_MODIFY, &nid);
#else
        // For other platforms - implement as needed
        std::cout << "NOTIFICATION: " << message << std::endl;
#endif
    }
};

class BatteryMonitor {
public:
    BatteryMonitor() : running(false), db(nullptr) {
        InitializeDatabase();
    }

    ~BatteryMonitor() {
        Stop();
        if (db) {
            sqlite3_close(db);
        }
    }

    void Start(int intervalSeconds = 60) {
        if (running) return;

        running = true;
        previouslyCharging = IsCharging();
        
        monitorThread = std::thread([this, intervalSeconds]() {
            while (running) {
                BatteryInfo info = GetBatteryInfo();
                
                // Store the data
                auto now = std::chrono::system_clock::now();
                time_t timestamp = std::chrono::system_clock::to_time_t(now);
                
                {
                    std::lock_guard<std::mutex> lock(dataMutex);
                    batteryHistory.push_back(std::make_pair(timestamp, info.percentage));
                    if (info.isCharging != previouslyCharging) {
                        if (info.isCharging) {
                            chargeEvents.push_back(std::make_pair(timestamp, info.percentage));
                        } else {
                            dischargeEvents.push_back(std::make_pair(timestamp, info.percentage));
                        }
                    }
                    
                    // Store to database
                    StoreBatteryData(timestamp, info);
                    
                    // Calculate statistics
                    UpdateStatistics();
                    
                    // Check for notifications
                    notificationManager.CheckNotifications(info.percentage, previouslyCharging, info.isCharging);
                    
                    previouslyCharging = info.isCharging;
                    currentBatteryInfo = info;
                }
                
                // Sleep for the interval
                std::this_thread::sleep_for(std::chrono::seconds(intervalSeconds));
            }
        });
    }

    void Stop() {
        if (!running) return;
        
        running = false;
        if (monitorThread.joinable()) {
            monitorThread.join();
        }
        
        // Save data
        SaveData();
    }

    BatteryInfo GetCurrentInfo() const {
        std::lock_guard<std::mutex> lock(dataMutex);
        return currentBatteryInfo;
    }

    std::vector<std::pair<time_t, float>> GetHistory(time_t startTime = 0, time_t endTime = 0) const {
        std::lock_guard<std::mutex> lock(dataMutex);
        
        if (startTime == 0 && endTime == 0) {
            return batteryHistory;
        }
        
        std::vector<std::pair<time_t, float>> filteredHistory;
        for (const auto& entry : batteryHistory) {
            if ((startTime == 0 || entry.first >= startTime) && 
                (endTime == 0 || entry.first <= endTime)) {
                filteredHistory.push_back(entry);
            }
        }
        
        return filteredHistory;
    }

    struct BatteryStatistics {
        float averageDischargePct; // percent per hour
        float averageChargePct;    // percent per hour
        long averageCycleTime;     // seconds for a full cycle
        float deepestDischarge;    // lowest percentage
        float lowestHealthPercent; // lowest health percentage recorded
    };

    BatteryStatistics GetStatistics() const {
        std::lock_guard<std::mutex> lock(dataMutex);
        return statistics;
    }

    NotificationManager& GetNotificationManager() {
        return notificationManager;
    }

private:
    bool running;
    bool previouslyCharging;
    std::thread monitorThread;
    mutable std::mutex dataMutex;
    
    BatteryInfo currentBatteryInfo;
    std::vector<std::pair<time_t, float>> batteryHistory;
    std::vector<std::pair<time_t, float>> chargeEvents;
    std::vector<std::pair<time_t, float>> dischargeEvents;
    
    BatteryStatistics statistics;
    NotificationManager notificationManager;
    
    sqlite3* db;

    void InitializeDatabase() {
        int rc = sqlite3_open("PowerPulse.db", &db);
        if (rc) {
            std::cerr << "Can't open database: " << sqlite3_errmsg(db) << std::endl;
            sqlite3_close(db);
            db = nullptr;
            return;
        }

        // Create tables if they don't exist
        const char* createTableSQL = 
            "CREATE TABLE IF NOT EXISTS battery_data ("
            "timestamp INTEGER PRIMARY KEY,"
            "percentage REAL,"
            "charging INTEGER,"
            "time_remaining INTEGER,"
            "health INTEGER,"
            "charge_rate REAL"
            ");";

        char* errMsg = nullptr;
        rc = sqlite3_exec(db, createTableSQL, nullptr, nullptr, &errMsg);
        if (rc != SQLITE_OK) {
            std::cerr << "SQL error: " << errMsg << std::endl;
            sqlite3_free(errMsg);
        }
    }

    void StoreBatteryData(time_t timestamp, const BatteryInfo& info) {
        if (!db) return;

        char sql[512];
        snprintf(sql, sizeof(sql), 
                "INSERT INTO battery_data VALUES(%lld, %.2f, %d, %ld, %d, %.2f);",
                static_cast<long long>(timestamp),
                info.percentage,
                info.isCharging ? 1 : 0,
                info.timeRemaining,
                info.health,
                info.chargeRate);

        char* errMsg = nullptr;
        int rc = sqlite3_exec(db, sql, nullptr, nullptr, &errMsg);
        if (rc != SQLITE_OK) {
            std::cerr << "SQL error: " << errMsg << std::endl;
            sqlite3_free(errMsg);
        }
    }

    void LoadHistoricalData() {
        if (!db) return;

        const char* sql = "SELECT timestamp, percentage FROM battery_data ORDER BY timestamp;";
        
        sqlite3_stmt* stmt;
        int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr);
        
        if (rc != SQLITE_OK) {
            std::cerr << "Failed to prepare statement: " << sqlite3_errmsg(db) << std::endl;
            return;
        }
        
        batteryHistory.clear();
        
        while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
            time_t timestamp = sqlite3_column_int64(stmt, 0);
            float percentage = static_cast<float>(sqlite3_column_double(stmt, 1));
            
            batteryHistory.push_back(std::make_pair(timestamp, percentage));
        }
        
        if (rc != SQLITE_DONE) {
            std::cerr << "Error reading data: " << sqlite3_errmsg(db) << std::endl;
        }
        
        sqlite3_finalize(stmt);
        
        // Also load charge/discharge events
        LoadChargeEvents();
    }

    void LoadChargeEvents() {
        if (!db) return;

        // Find charging state changes
        const char* sql = 
            "SELECT a.timestamp, a.percentage "
            "FROM battery_data a, battery_data b "
            "WHERE a.rowid = b.rowid + 1 AND a.charging != b.charging "
            "ORDER BY a.timestamp;";
        
        sqlite3_stmt* stmt;
        int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr);
        
        if (rc != SQLITE_OK) {
            std::cerr << "Failed to prepare statement: " << sqlite3_errmsg(db) << std::endl;
            return;
        }
        
        chargeEvents.clear();
        dischargeEvents.clear();
        
        // We need to determine the starting state first
        bool isCurrentlyCharging = IsCharging();
        bool previousStateCharging = !isCurrentlyCharging; // Opposite to ensure we record the first state change
        
        while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
            time_t timestamp = sqlite3_column_int64(stmt, 0);
            float percentage = static_cast<float>(sqlite3_column_double(stmt, 1));
            
            // Toggle the state
            previousStateCharging = !previousStateCharging;
            
            if (previousStateCharging) {
                chargeEvents.push_back(std::make_pair(timestamp, percentage));
            } else {
                dischargeEvents.push_back(std::make_pair(timestamp, percentage));
            }
        }
        
        if (rc != SQLITE_DONE) {
            std::cerr << "Error reading data: " << sqlite3_errmsg(db) << std::endl;
        }
        
        sqlite3_finalize(stmt);
    }

    void SaveData() {
        // Data is already saved to SQLite during monitoring
        // This function could be used for any additional cleanup or exports
    }

    void UpdateStatistics() {
        if (batteryHistory.size() < 2) return;
        
        // Calculate discharge rate
        float totalDischargePct = 0.0f;
        int dischargeCount = 0;
        time_t lastDischargeTime = 0;
        float lastDischargePercentage = 0.0f;
        
        // Calculate charge rate
        float totalChargePct = 0.0f;
        int chargeCount = 0;
        time_t lastChargeTime = 0;
        float lastChargePercentage = 0.0f;
        
        // Track lowest values
        float lowestPercentage = 100.0f;
        float lowestHealth = 100.0f;
        
        for (size_t i = 1; i < batteryHistory.size(); ++i) {
            time_t t1 = batteryHistory[i-1].first;
            time_t t2 = batteryHistory[i].first;
            float p1 = batteryHistory[i-1].second;
            float p2 = batteryHistory[i].second;
            
            if (p2 < lowestPercentage) {
                lowestPercentage = p2;
            }
            
            // This would need actual health metrics from the battery
            // For now we'll just use the current health
            if (currentBatteryInfo.health < lowestHealth) {
                lowestHealth = static_cast<float>(currentBatteryInfo.health);
            }
            
            // Calculate rate of change (percent per hour)
            float hoursDiff = static_cast<float>(t2 - t1) / 3600.0f;
            if (hoursDiff > 0) {
                float ratePctPerHour = (p2 - p1) / hoursDiff;
                
                if (ratePctPerHour < 0) {
                    // Discharging
                    totalDischargePct += -ratePctPerHour;
                    dischargeCount++;
                    
                    lastDischargeTime = t2;
                    lastDischargePercentage = p2;
                } else if (ratePctPerHour > 0) {
                    // Charging
                    totalChargePct += ratePctPerHour;
                    chargeCount++;
                    
                    lastChargeTime = t2;
                    lastChargePercentage = p2;
                }
            }
        }
        
        // Calculate average rates
        statistics.averageDischargePct = dischargeCount > 0 ? totalDischargePct / dischargeCount : 0.0f;
        statistics.averageChargePct = chargeCount > 0 ? totalChargePct / chargeCount : 0.0f;
        
        // Estimate full cycle time
        if (statistics.averageDischargePct > 0 && statistics.averageChargePct > 0) {
            float hoursToDischarge = 100.0f / statistics.averageDischargePct;
            float hoursToCharge = 100.0f / statistics.averageChargePct;
            statistics.averageCycleTime = static_cast<long>((hoursToDischarge + hoursToCharge) * 3600.0f);
        } else {
            statistics.averageCycleTime = -1; // Unknown
        }
        
        statistics.deepestDischarge = lowestPercentage;
        statistics.lowestHealthPercent = lowestHealth;
    }

    BatteryInfo GetBatteryInfo() {
        BatteryInfo info;
        
#ifdef _WIN32
        SYSTEM_POWER_STATUS status;
        if (GetSystemPowerStatus(&status)) {
            info.percentage = status.BatteryLifePercent;
            info.isCharging = status.ACLineStatus == 1;
            info.timeRemaining = status.BatteryLifeTime;
            
            // We need to use Windows Management Instrumentation (WMI) for health and charge rate
            // This is simplified for this example
            info.health = 100; // Placeholder
            info.chargeRate = info.isCharging ? 15.0f : -10.0f; // Placeholder values
        } else {
            info.percentage = 0;
            info.isCharging = false;
            info.timeRemaining = -1;
            info.health = 0;
            info.chargeRate = 0;
        }
#else
        // Implement for other platforms
        info.percentage = 0;
        info.isCharging = false;
        info.timeRemaining = -1;
        info.health = 0;
        info.chargeRate = 0;
#endif

        return info;
    }

    bool IsCharging() {
#ifdef _WIN32
        SYSTEM_POWER_STATUS status;
        if (GetSystemPowerStatus(&status)) {
            return status.ACLineStatus == 1;
        }
#endif
        return false;
    }
};

// Forward declare the GUI class to allow CLI mode
class PowerPulseGUI;

// CLI implementation
class PowerPulseCLI {
public:
    PowerPulseCLI(std::shared_ptr<BatteryMonitor> monitor) : monitor(monitor) {}

    void Run() {
        std::cout << "PowerPulse CLI v" << APP_VERSION << std::endl;
        std::cout << "Type 'help' for a list of commands." << std::endl;

        std::string command;
        while (true) {
            std::cout << "> ";
            std::getline(std::cin, command);

            if (command == "exit" || command == "quit") {
                break;
            } else if (command == "info") {
                ShowBatteryInfo();
            } else if (command == "stats") {
                ShowStatistics();
            } else if (command == "history") {
                ShowHistory();
            } else if (command == "start") {
                monitor->Start();
                std::cout << "Monitoring started." << std::endl;
            } else if (command == "stop") {
                monitor->Stop();
                std::cout << "Monitoring stopped." << std::endl;
            } else if (command == "gui") {
                std::cout << "GUI mode not available in CLI session." << std::endl;
            } else if (command.substr(0, 9) == "threshold") {
                HandleThresholdCommand(command);
            } else if (command == "help") {
                ShowHelp();
            } else {
                std::cout << "Unknown command. Type 'help' for a list of commands." << std::endl;
            }
        }
    }

private:
    std::shared_ptr<BatteryMonitor> monitor;

    void ShowBatteryInfo() {
        BatteryInfo info = monitor->GetCurrentInfo();
        std::cout << "Battery Status:" << std::endl;
        std::cout << "  Percentage: " << info.percentage << "%" << std::endl;
        std::cout << "  State: " << (info.isCharging ? "Charging" : "Discharging") << std::endl;
        
        if (info.timeRemaining > 0) {
            int hours = info.timeRemaining / 3600;
            int minutes = (info.timeRemaining % 3600) / 60;
            std::cout << "  Time remaining: " << hours << "h " << minutes << "m" << std::endl;
        } else {
            std::cout << "  Time remaining: Unknown" << std::endl;
        }
        
        std::cout << "  Health: " << info.health << "%" << std::endl;
        std::cout << "  Charge rate: " << std::abs(info.chargeRate) << "W" 
                  << (info.chargeRate > 0 ? " (in)" : " (out)") << std::endl;
    }

    void ShowStatistics() {
        auto stats = monitor->GetStatistics();
        std::cout << "Battery Statistics:" << std::endl;
        std::cout << "  Average discharge rate: " << stats.averageDischargePct << "% per hour" << std::endl;
        std::cout << "  Average charge rate: " << stats.averageChargePct << "% per hour" << std::endl;
        
        if (stats.averageCycleTime > 0) {
            int hours = stats.averageCycleTime / 3600;
            int minutes = (stats.averageCycleTime % 3600) / 60;
            std::cout << "  Average cycle time: " << hours << "h " << minutes << "m" << std::endl;
        } else {
            std::cout << "  Average cycle time: Unknown" << std::endl;
        }
        
        std::cout << "  Deepest discharge: " << stats.deepestDischarge << "%" << std::endl;
        std::cout << "  Lowest health: " << stats.lowestHealthPercent << "%" << std::endl;
    }

    void ShowHistory() {
        // Show the last 10 entries
        auto history = monitor->GetHistory();
        
        if (history.empty()) {
            std::cout << "No history available." << std::endl;
            return;
        }
        
        std::cout << "Battery History (Last 10 entries):" << std::endl;
        std::cout << "  Time                  | Percentage" << std::endl;
        std::cout << "  ----------------------|------------" << std::endl;
        
        int count = 0;
        for (auto it = history.rbegin(); it != history.rend() && count < 10; ++it, ++count) {
            char buffer[30];
            std::strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", std::localtime(&it->first));
            std::cout << "  " << buffer << " | " << it->second << "%" << std::endl;
        }
    }

    void HandleThresholdCommand(const std::string& command) {
        // Parse the command: threshold <type> <value>
        std::istringstream iss(command);
        std::string cmd, type;
        float value;
        
        iss >> cmd >> type >> value;
        
        if (type.empty() || value < 0 || value > 100) {
            std::cout << "Invalid syntax. Use 'threshold <type> <value>'" << std::endl;
            return;
        }
        
        NotificationManager& nm = monitor->GetNotificationManager();
        
        if (type == "critical") {
            nm.SetThreshold(NotificationManager::CRITICAL_LOW, value);
        } else if (type == "low") {
            nm.SetThreshold(NotificationManager::LOW, value);
        } else if (type == "optimal") {
            nm.SetThreshold(NotificationManager::OPTIMAL_CHARGE_REACHED, value);
        } else if (type == "full") {
            nm.SetThreshold(NotificationManager::FULLY_CHARGED, value);
        } else if (type == "custom") {
            std::string message;
            std::getline(iss, message);
            if (!message.empty()) {
                nm.AddCustomThreshold(value, message);
            } else {
                std::cout << "Custom threshold requires a message." << std::endl;
                return;
            }
        } else {
            std::cout << "Unknown threshold type. Use critical, low, optimal, full, or custom." << std::endl;
            return;
        }
        
        std::cout << "Threshold updated." << std::endl;
    }

    void ShowHelp() {
        std::cout << "Available commands:" << std::endl;
        std::cout << "  info      - Show current battery information" << std::endl;
        std::cout << "  stats     - Show battery statistics" << std::endl;
        std::cout << "  history   - Show battery history (last 10 entries)" << std::endl;
        std::cout << "  start     - Start monitoring" << std::endl;
        std::cout << "  stop      - Stop monitoring" << std::endl;
        std::cout << "  threshold <type> <value> [message] - Set notification threshold" << std::endl;
        std::cout << "             Types: critical, low, optimal, full, custom" << std::endl;
        std::cout << "  gui       - Switch to GUI mode (not available in CLI session)" << std::endl;
        std::cout << "  help      - Show this help message" << std::endl;
        std::cout << "  exit      - Exit the application" << std::endl;
    }
};

// Main GUI implementation (using Dear ImGui)
class PowerPulseGUI {
public:
    PowerPulseGUI(std::shared_ptr<BatteryMonitor> monitor) : monitor(monitor), running(false) {}

    bool Initialize() {
        // Create application window
        WNDCLASSEX wc = { sizeof(WNDCLASSEX), CS_CLASSDC, WndProc, 0L, 0L, GetModuleHandle(NULL), NULL, NULL, NULL, NULL, _T("PowerPulse"), NULL };
        RegisterClassEx(&wc);
        hwnd = CreateWindow(wc.lpszClassName, _T("PowerPulse"), WS_OVERLAPPEDWINDOW, 100, 100, 1024, 768, NULL, NULL, wc.hInstance, NULL);

        // Initialize Direct3D
        if (!CreateDeviceD3D(hwnd)) {
            CleanupDeviceD3D();
            UnregisterClass(wc.lpszClassName, wc.hInstance);
            return false;
        }

        // Show the window
        ShowWindow(hwnd, SW_SHOWDEFAULT);
        UpdateWindow(hwnd);

        // Setup Dear ImGui context
        IMGUI_CHECKVERSION();
        ImGui::CreateContext();
        ImGuiIO& io = ImGui::GetIO();
        io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;  // Enable Keyboard Controls
        io.ConfigFlags |= ImGuiConfigFlags_DockingEnable;      // Enable Docking
        io.ConfigFlags |= ImGuiConfigFlags_ViewportsEnable;    // Enable Multi-Viewport

        // Setup Platform/Renderer backends
        ImGui_ImplWin32_Init(hwnd);
        ImGui_ImplDX11_Init(g_pd3dDevice, g_pd3dDeviceContext);

        // Add system tray icon
        NOTIFYICONDATAA nid = { sizeof(nid) };
        nid.hWnd = hwnd;
        nid.uID = 1;
        nid.uFlags = NIF_ICON | NIF_MESSAGE | NIF_TIP;
        nid.uCallbackMessage = WM_USER + 1;
        nid.hIcon = LoadIcon(NULL, IDI_APPLICATION);
        strcpy_s(nid.szTip, "PowerPulse");
        Shell_NotifyIconA(NIM_ADD, &nid);

        return true;
    }

    void Run() {
        running = true;
        lastUpdateTime = std::chrono::steady_clock::now();

        // Start the monitoring
        monitor->Start();

        // Main loop
        MSG msg;
        ZeroMemory(&msg, sizeof(msg));
        while (running && msg.message != WM_QUIT) {
            if (PeekMessage(&msg, NULL, 0U, 0U, PM_REMOVE)) {
                TranslateMessage(&msg);
                DispatchMessage(&msg);
                continue;
            }

            // Start the Dear ImGui frame
            ImGui_ImplDX11_NewFrame();
            ImGui_ImplWin32_NewFrame();
            ImGui::NewFrame();

            RenderUI();

            // Rendering
            ImGui::Render();
            const float clear_color_with_alpha[4] = { 0.0f, 0.0f, 0.0f, 1.0f };
            g_pd3dDeviceContext->OMSetRenderTargets(1, &g_mainRenderTargetView, NULL);
            g_pd3dDeviceContext->ClearRenderTargetView(g_mainRenderTargetView, clear_color_with_alpha);
            ImGui_ImplDX11_RenderDrawData(ImGui::GetDrawData());

            // Update and Render additional Platform Windows
            if (ImGui::GetIO().ConfigFlags & ImGuiConfigFlags_ViewportsEnable) {
                ImGui::UpdatePlatformWindows();
                ImGui::RenderPlatformWindowsDefault();
            }

            g_pSwapChain->Present(1, 0); // Present with vsync
        }
