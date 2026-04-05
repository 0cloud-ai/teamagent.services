"use client";

import { useEffect } from "react";
import { FolderOpen, ChevronLeft } from "lucide-react";
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuBadge,
} from "@/components/ui/sidebar";
import { useWorkspaceStore } from "@/stores/workspace-store";

export function DirectoryTree() {
  const { currentPath, children, setPath, fetchStats } = useWorkspaceStore();

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const isRoot = currentPath === "/";

  return (
    <SidebarGroup>
      <SidebarGroupLabel>Explorer</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          {!isRoot && (
            <SidebarMenuItem>
              <SidebarMenuButton
                onClick={() => {
                  const parent = currentPath.replace(/\/[^/]+\/?$/, "") || "/";
                  setPath(parent);
                }}
              >
                <ChevronLeft className="size-4" />
                <span>..</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          )}
          <SidebarMenuItem>
            <SidebarMenuButton isActive>
              <FolderOpen className="size-4" />
              <span>{currentPath === "/" ? "/" : currentPath.split("/").pop()}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
          {children.map((child) => (
            <SidebarMenuItem key={child.name}>
              <SidebarMenuButton
                onClick={() => {
                  const next = currentPath === "/"
                    ? `/${child.name}`
                    : `${currentPath}/${child.name}`;
                  setPath(next);
                }}
                className="pl-6"
              >
                <FolderOpen className="size-4" />
                <span>{child.name}</span>
                {child.total.sessions > 0 && (
                  <SidebarMenuBadge>{child.total.sessions}</SidebarMenuBadge>
                )}
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}
