import { load } from "@tauri-apps/plugin-store";
import { appDataDir, join } from "@tauri-apps/api/path";

const SETTINGS_FILE = "settings.json";

interface AppSettings {
    OBSIDIAN_OV_MODEL_DIR: string;
    HF_HOME: string;
}

// Defaults are now calculated dynamically
const DEFAULT_SUBDIRS = {
    OV_MODELS: "ov_models",
    HF_CACHE: "hf_cache"
};

export class SettingsManager {
    private static store: Awaited<ReturnType<typeof load>> | null = null;

    private static async getStore() {
        if (!this.store) {
            const appData = await appDataDir();
            console.log("SettingsManager: AppData Dir is:", appData);
            console.log("SettingsManager: Full Path should be:", await join(appData, SETTINGS_FILE));
            this.store = await load(SETTINGS_FILE, { autoSave: true, defaults: {} });
        }
        return this.store;
    }

    static async initialize(): Promise<AppSettings> {
        const store = await this.getStore();
        const appData = await appDataDir();

        // Dynamic Defaults based on AppData
        const defaultOvDir = await join(appData, DEFAULT_SUBDIRS.OV_MODELS);
        const defaultHfHome = await join(appData, DEFAULT_SUBDIRS.HF_CACHE);

        // Check if keys exist, if not set defaults
        const ovDir = await store.get<string>("OBSIDIAN_OV_MODEL_DIR");
        const hfHome = await store.get<string>("HF_HOME");

        let finalSettings: AppSettings = {
            OBSIDIAN_OV_MODEL_DIR: ovDir || defaultOvDir,
            HF_HOME: hfHome || defaultHfHome
        };

        if (!ovDir) {
            await store.set("OBSIDIAN_OV_MODEL_DIR", defaultOvDir);
        }

        if (!hfHome) {
            await store.set("HF_HOME", defaultHfHome);
        }

        await store.save();
        console.log("SettingsManager: Settings saved to store.");
        return finalSettings;
    }

    static async getSettings(): Promise<AppSettings> {
        const store = await this.getStore();
        // Fallback or read from store. Since initialize guarantees set, this is safe.
        // Re-calculating defaults here would be redundant but safe.
        // For simplicity, we assume initialize() was called or we return what's in store.

        // If we want robust fallback without initialize:
        const appData = await appDataDir();
        const defaultOvDir = await join(appData, DEFAULT_SUBDIRS.OV_MODELS);
        const defaultHfHome = await join(appData, DEFAULT_SUBDIRS.HF_CACHE);

        return {
            OBSIDIAN_OV_MODEL_DIR: (await store.get("OBSIDIAN_OV_MODEL_DIR")) || defaultOvDir,
            HF_HOME: (await store.get("HF_HOME")) || defaultHfHome,
        };
    }
}
