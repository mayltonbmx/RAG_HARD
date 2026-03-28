"use client";

import { useState } from "react";
import { ViewType } from "@/types";
import Sidebar from "@/components/Sidebar";
import ChatView from "@/components/ChatView";
import StatsView from "@/components/StatsView";

export default function Home() {
  const [activeView, setActiveView] = useState<ViewType>("chat");

  return (
    <div className="app-layout">
      <Sidebar
        activeView={activeView}
        onViewChange={setActiveView}
        onNewChat={() => {
          setActiveView("stats");
          setTimeout(() => setActiveView("chat"), 0);
        }}
      />
      <main className="main-content">
        {activeView === "chat" && <ChatView />}
        {activeView === "stats" && <StatsView />}
      </main>
    </div>
  );
}
