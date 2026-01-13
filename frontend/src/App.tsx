import { useEffect } from "react";
import "./index.css";
import { Sidebar } from "./components/Sidebar";
import { ChatArea } from "./components/ChatArea";
import { Command } from "@tauri-apps/plugin-shell";
import { SettingsManager } from "./utils/SettingsManager";

function App() {
  useEffect(() => {
    const startBackend = async () => {
      try {
        console.log("Loading settings...");
        const settings = await SettingsManager.initialize();

        if (import.meta.env.DEV) {
          console.log("Skipping backend sidecar in development mode");
          return;
        }

        console.log("Attempting to spawn backend sidecar...");
        const command = Command.sidecar("binaries/backend", [], {
          env: {
            "OBSIDIAN_OV_MODEL_DIR": settings.OBSIDIAN_OV_MODEL_DIR,
            "HF_HOME": settings.HF_HOME
          }
        });
        const child = await command.spawn();
        console.log("Backend spawned with PID:", child.pid);

        // Optional: Listen to stdout for debugging
        command.stdout.on("data", (line) => console.log(`[BACKEND]: ${line}`));
        command.stderr.on("data", (line) => console.error(`[BACKEND ERR]: ${line}`));

      } catch (error) {
        console.error("Failed to spawn backend sidecar:", error);
      }
    };

    startBackend();
  }, []);

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-[var(--bg-primary)] text-[var(--text-primary)]">
      <Sidebar />
      <main className="flex-1 h-full min-w-0 flex flex-col relative">
        <ChatArea />
      </main>
    </div>
  );
}

export default App;
