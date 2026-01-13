import "./index.css";
import { Sidebar } from "./components/Sidebar";
import { ChatArea } from "./components/ChatArea";

function App() {
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
