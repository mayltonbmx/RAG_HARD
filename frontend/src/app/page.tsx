"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { ViewType } from "@/types";
import Sidebar from "@/components/Sidebar";
import ChatView from "@/components/ChatView";
import StatsView from "@/components/StatsView";
import UploadView from "@/components/UploadView";
import FilesView from "@/components/FilesView";

export default function Home() {
  const [activeView, setActiveView] = useState<ViewType>("chat");
  const { data: session } = useSession();

  const roles: string[] = session?.roles ?? [];
  const isAdmin = roles.includes("Admin");

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
        {activeView === "upload" && isAdmin && <UploadView />}
        {activeView === "files" && isAdmin && <FilesView />}
      </main>
    </div>
  );
}
