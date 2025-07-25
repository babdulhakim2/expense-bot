"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useBusiness } from "@/app/providers/BusinessProvider";
import { ArrowRight, Building, LogOut, Settings } from "lucide-react";
import { signOut, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";

export function AccountMenu() {
  const { data: session } = useSession();
  const router = useRouter();

  // Use the enhanced business context
  const { currentBusiness, loadingStates } = useBusiness();

  if (!session?.user) return null;

  const handleLogout = async () => {
    await signOut({ callbackUrl: "/" });
  };

  const handleGoToDashboard = () => {
    router.push("/dashboard");
  };

  const getInitials = (name?: string | null) => {
    if (!name) return "U";
    return name
      .split(" ")
      .map((word) => word[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="flex items-center space-x-3">
      {/* Quick Dashboard Access */}
      {currentBusiness && !loadingStates && (
        <Button
          onClick={handleGoToDashboard}
          variant="outline"
          size="sm"
          className="hidden sm:flex items-center space-x-2"
        >
          <Building className="w-4 h-4" />
          <span>Dashboard</span>
          <ArrowRight className="w-3 h-3" />
        </Button>
      )}

      {/* Account Dropdown */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="relative h-10 w-10 rounded-full">
            <Avatar className="h-10 w-10">
              <AvatarImage
                src={session.user.name || undefined}
                alt={session.user.name || ""}
              />
              <AvatarFallback className="bg-primary/10 text-primary font-medium">
                {getInitials(session.user.name)}
              </AvatarFallback>
            </Avatar>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-64" align="end" forceMount>
          <DropdownMenuLabel className="font-normal">
            <div className="flex flex-col space-y-1">
              <p className="text-sm font-medium leading-none">
                {session.user.name || "User"}
              </p>
              <p className="text-xs leading-none text-muted-foreground">
                {session.user.email}
              </p>
              {currentBusiness && (
                <div className="flex items-center space-x-1 mt-2 pt-2 border-t">
                  <Building className="w-3 h-3 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">
                    {currentBusiness.name}
                  </span>
                </div>
              )}
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />

          {/* Dashboard Link */}
          <DropdownMenuItem onClick={handleGoToDashboard}>
            <Building className="mr-2 h-4 w-4" />
            <span>Dashboard</span>
          </DropdownMenuItem>

          {/* Settings Link */}
          <DropdownMenuItem onClick={() => router.push("/dashboard/settings")}>
            <Settings className="mr-2 h-4 w-4" />
            <span>Settings</span>
          </DropdownMenuItem>

          <DropdownMenuSeparator />

          {/* Logout */}
          <DropdownMenuItem
            onClick={handleLogout}
            className="text-red-600 focus:text-red-600"
          >
            <LogOut className="mr-2 h-4 w-4" />
            <span>Log out</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
