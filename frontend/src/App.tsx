import { useState } from "react";
import Board from "./views/Board";
import Explorer from "./views/Explorer";
import Performance from "./views/Performance";

type Tab = "board" | "performance" | "explorer";

const TABS: { id: Tab; label: string }[] = [
  { id: "board", label: "Board" },
  { id: "performance", label: "Track record" },
  { id: "explorer", label: "Explorer" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("board");
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          Outscaled<span>.GG</span>
        </div>
        <nav className="tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`tab ${tab === t.id ? "active" : ""}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
        <div className="meta">series-level props model · paper-trade mode</div>
      </header>
      {tab === "board" && <Board />}
      {tab === "performance" && <Performance />}
      {tab === "explorer" && <Explorer />}
    </div>
  );
}
