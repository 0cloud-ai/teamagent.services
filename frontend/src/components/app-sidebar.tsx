"use client";

import * as React from "react";
import { FolderOpen, Database, Plug } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { WorkspaceSwitcher } from "@/components/workspace-switcher";
import { NavUser } from "@/components/nav-user";
import { DirectoryTree } from "@/components/directory-tree";
import { useUIStore } from "@/stores/ui-store";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { activeTab, setActiveTab } = useUIStore();

  return (
    <Sidebar {...props}>
      <SidebarHeader>
        <WorkspaceSwitcher />
        <Tabs
          value={activeTab}
          onValueChange={(v) => setActiveTab(v as "files" | "datas" | "services")}
          className="w-full"
        >
          <TabsList className="w-full">
            <TabsTrigger value="files" className="flex-1">
              <FolderOpen className="size-4" />
            </TabsTrigger>
            <TabsTrigger value="datas" className="flex-1">
              <Database className="size-4" />
            </TabsTrigger>
            <TabsTrigger value="services" className="flex-1">
              <Plug className="size-4" />
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </SidebarHeader>
      <SidebarContent>
        {activeTab === "files" && <DirectoryTree />}
        {activeTab === "datas" && (
          <div className="flex flex-1 items-center justify-center p-4 text-sm text-muted-foreground">
            Datas — TODO
          </div>
        )}
        {activeTab === "services" && (
          <div className="flex flex-1 items-center justify-center p-4 text-sm text-muted-foreground">
            Services — TODO
          </div>
        )}
      </SidebarContent>
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
