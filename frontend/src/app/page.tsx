"use client";

import { useState, useRef } from "react";
import { ViewType } from "@/types";
import Sidebar from "@/components/Sidebar";
import ChatView from "@/components/ChatView";
import UploadView from "@/components/UploadView";
import FilesView from "@/components/FilesView";
import StatsView from "@/components/StatsView";

export default function Home() {
  const [activeView, setActiveView] = useState<ViewType>("chat");
  const chatViewRef = useRef<{ handleNewChat: () => void }>(null);

  return (
    <div className="app-layout">
      <Sidebar
        activeView={activeView}
        onViewChange={setActiveView}
        onNewChat={() => {
          setActiveView("chat");
          // Force remount of ChatView to reset state
          setActiveView("stats");
          setTimeout(() => setActiveView("chat"), 0);
        }}
      />
      <main className="main-content">
        {activeView === "chat" && <ChatView />}
        {activeView === "upload" && <UploadView />}
        {activeView === "files" && <FilesView />}
        {activeView === "stats" && <StatsView />}
      </main>
    </div>
  );
}
