"use client";

import { useState, useEffect } from "react";
import { ViewType } from "@/types";
import { getAdminToken } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import ChatView from "@/components/ChatView";
import StatsView from "@/components/StatsView";
import UploadView from "@/components/UploadView";
import FilesView from "@/components/FilesView";
import AnalyticsView from "@/components/AnalyticsView";
import PersonasView from "@/components/PersonasView";
import AdminLoginScreen from "@/components/AdminLoginScreen";

export default function Home() {
  const [activeView, setActiveView] = useState<ViewType>("chat");
  const [isAdminLoggedIn, setIsAdminLoggedIn] = useState(false);

  // Check for existing admin JWT on mount
  useEffect(() => {
    const token = getAdminToken();
    if (token) {
      setIsAdminLoggedIn(true);
    }
  }, []);

  const isAdmin = isAdminLoggedIn;

  const handleAdminLoginSuccess = () => {
    setIsAdminLoggedIn(true);
    setActiveView("analytics");
  };

  const handleAdminLogout = () => {
    setIsAdminLoggedIn(false);
    setActiveView("chat");
  };

  // Show admin login screen if trying to access admin views without auth
  const needsAdminLogin = !isAdmin && ["analytics", "upload", "files", "personas"].includes(activeView);

  return (
    <div className="app-layout">
      <Sidebar
        activeView={activeView}
        onViewChange={setActiveView}
        onNewChat={() => {
          setActiveView("stats");
          setTimeout(() => setActiveView("chat"), 0);
        }}
        isAdminLoggedIn={isAdminLoggedIn}
        onAdminLogout={handleAdminLogout}
      />
      <main className="main-content">
        {activeView === "chat" && <ChatView isLoggedIn={isAdmin} />}
        {activeView === "stats" && <StatsView />}
        {needsAdminLogin && <AdminLoginScreen onLoginSuccess={handleAdminLoginSuccess} />}
        {activeView === "analytics" && isAdmin && <AnalyticsView />}
        {activeView === "upload" && isAdmin && <UploadView />}
        {activeView === "files" && isAdmin && <FilesView />}
        {activeView === "personas" && isAdmin && <PersonasView />}
      </main>
    </div>
  );
}
