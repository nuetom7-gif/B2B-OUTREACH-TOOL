import { _ as useWorkspaceProfile, a as useContacts, n as useCompanies, x as cn } from "./hooks-xnZ2zKrZ.js";
import * as React from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { HeadContent, Link, Outlet, Scripts, createFileRoute, createRootRouteWithContext, createRouter, lazyRouteComponent, useNavigate, useRouter, useRouterState } from "@tanstack/react-router";
import { jsx, jsxs } from "react/jsx-runtime";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BarChart3, Bell, Building, Building2, Check, ChevronRight, ChevronsUpDown, Circle, ClipboardList, FileBarChart, FileText, Inbox, LayoutDashboard, LogOut, Mail, Moon, MoreHorizontal, PanelLeft, Radar, Search, Settings, ShieldCheck, Sun, User, Users, X } from "lucide-react";
import { Slot } from "@radix-ui/react-slot";
import { cva } from "class-variance-authority";
import * as SeparatorPrimitive from "@radix-ui/react-separator";
import * as SheetPrimitive from "@radix-ui/react-dialog";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { Command } from "cmdk";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import * as PopoverPrimitive from "@radix-ui/react-popover";
import * as AvatarPrimitive from "@radix-ui/react-avatar";
import { Toaster } from "sonner";
//#region \0rolldown/runtime.js
var __defProp = Object.defineProperty;
var __exportAll = (all, no_symbols) => {
	let target = {};
	for (var name in all) __defProp(target, name, {
		get: all[name],
		enumerable: true
	});
	if (!no_symbols) __defProp(target, Symbol.toStringTag, { value: "Module" });
	return target;
};
//#endregion
//#region src/styles.css?url
var styles_default = "/assets/styles-trTZHx3M.css";
//#endregion
//#region src/lib/lovable-error-reporting.ts
function reportLovableError(error, context = {}) {
	if (typeof window === "undefined") return;
	window.__lovableEvents?.captureException?.(error, {
		source: "react_error_boundary",
		route: window.location.pathname,
		...context
	}, {
		mechanism: "react_error_boundary",
		handled: false,
		severity: "error"
	});
	const message = error instanceof Response ? `Response ${error.status}${error.url ? ` at ${error.url}` : ""}` : error instanceof Error ? error.message : String(error);
	const stack = error instanceof Error ? error.stack : void 0;
	window.__lovableReportRuntimeError?.({
		message,
		...stack !== void 0 && { stack },
		filename: window.location.pathname
	});
}
//#endregion
//#region src/lib/theme.tsx
var ThemeContext = createContext({
	theme: "light",
	toggle: () => {}
});
var KEY = "yash.outreach.theme";
function ThemeProvider({ children }) {
	const [theme, setTheme] = useState("light");
	useEffect(() => {
		const initial = window.localStorage.getItem(KEY) ?? (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
		setTheme(initial);
	}, []);
	useEffect(() => {
		document.documentElement.classList.toggle("dark", theme === "dark");
		window.localStorage.setItem(KEY, theme);
	}, [theme]);
	const toggle = useCallback(() => setTheme((t) => t === "dark" ? "light" : "dark"), []);
	return /* @__PURE__ */ jsx(ThemeContext.Provider, {
		value: {
			theme,
			toggle
		},
		children
	});
}
var useTheme = () => useContext(ThemeContext);
//#endregion
//#region src/hooks/use-mobile.tsx
var MOBILE_BREAKPOINT = 768;
function useIsMobile() {
	const [isMobile, setIsMobile] = React.useState(void 0);
	React.useEffect(() => {
		const mql = window.matchMedia(`(max-width: 767px)`);
		const onChange = () => {
			setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
		};
		mql.addEventListener("change", onChange);
		setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
		return () => mql.removeEventListener("change", onChange);
	}, []);
	return !!isMobile;
}
//#endregion
//#region src/components/ui/button.tsx
var buttonVariants = cva("inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0", {
	variants: {
		variant: {
			default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
			destructive: "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
			outline: "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
			secondary: "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
			ghost: "hover:bg-accent hover:text-accent-foreground",
			link: "text-primary underline-offset-4 hover:underline"
		},
		size: {
			default: "h-9 px-4 py-2",
			sm: "h-8 rounded-md px-3 text-xs",
			lg: "h-10 rounded-md px-8",
			icon: "h-9 w-9"
		}
	},
	defaultVariants: {
		variant: "default",
		size: "default"
	}
});
var Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
	return /* @__PURE__ */ jsx(asChild ? Slot : "button", {
		className: cn(buttonVariants({
			variant,
			size,
			className
		})),
		ref,
		...props
	});
});
Button.displayName = "Button";
//#endregion
//#region src/components/ui/input.tsx
var Input = React.forwardRef(({ className, type, ...props }, ref) => {
	return /* @__PURE__ */ jsx("input", {
		type,
		className: cn("flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm", className),
		ref,
		...props
	});
});
Input.displayName = "Input";
//#endregion
//#region src/components/ui/separator.tsx
var Separator = React.forwardRef(({ className, orientation = "horizontal", decorative = true, ...props }, ref) => /* @__PURE__ */ jsx(SeparatorPrimitive.Root, {
	ref,
	decorative,
	orientation,
	className: cn("shrink-0 bg-border", orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]", className),
	...props
}));
Separator.displayName = SeparatorPrimitive.Root.displayName;
//#endregion
//#region src/components/ui/sheet.tsx
var Sheet = SheetPrimitive.Root;
var SheetPortal = SheetPrimitive.Portal;
var SheetOverlay = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(SheetPrimitive.Overlay, {
	className: cn("fixed inset-0 z-50 bg-black/80  data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0", className),
	...props,
	ref
}));
SheetOverlay.displayName = SheetPrimitive.Overlay.displayName;
var sheetVariants = cva("fixed z-50 gap-4 bg-background p-6 shadow-lg transition ease-in-out data-[state=closed]:duration-300 data-[state=open]:duration-500 data-[state=open]:animate-in data-[state=closed]:animate-out", {
	variants: { side: {
		top: "inset-x-0 top-0 border-b data-[state=closed]:slide-out-to-top data-[state=open]:slide-in-from-top",
		bottom: "inset-x-0 bottom-0 border-t data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom",
		left: "inset-y-0 left-0 h-full w-3/4 border-r data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left sm:max-w-sm",
		right: "inset-y-0 right-0 h-full w-3/4 border-l data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right sm:max-w-sm"
	} },
	defaultVariants: { side: "right" }
});
var SheetContent = React.forwardRef(({ side = "right", className, children, ...props }, ref) => /* @__PURE__ */ jsxs(SheetPortal, { children: [/* @__PURE__ */ jsx(SheetOverlay, {}), /* @__PURE__ */ jsxs(SheetPrimitive.Content, {
	ref,
	className: cn(sheetVariants({ side }), className),
	...props,
	children: [/* @__PURE__ */ jsxs(SheetPrimitive.Close, {
		className: "absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background cursor-pointer transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-secondary",
		children: [/* @__PURE__ */ jsx(X, { className: "h-4 w-4" }), /* @__PURE__ */ jsx("span", {
			className: "sr-only",
			children: "Close"
		})]
	}), children]
})] }));
SheetContent.displayName = SheetPrimitive.Content.displayName;
var SheetHeader = ({ className, ...props }) => /* @__PURE__ */ jsx("div", {
	className: cn("flex flex-col space-y-2 text-center sm:text-left", className),
	...props
});
SheetHeader.displayName = "SheetHeader";
var SheetFooter = ({ className, ...props }) => /* @__PURE__ */ jsx("div", {
	className: cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2", className),
	...props
});
SheetFooter.displayName = "SheetFooter";
var SheetTitle = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(SheetPrimitive.Title, {
	ref,
	className: cn("text-lg font-semibold text-foreground", className),
	...props
}));
SheetTitle.displayName = SheetPrimitive.Title.displayName;
var SheetDescription = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(SheetPrimitive.Description, {
	ref,
	className: cn("text-sm text-muted-foreground", className),
	...props
}));
SheetDescription.displayName = SheetPrimitive.Description.displayName;
//#endregion
//#region src/components/ui/skeleton.tsx
function Skeleton({ className, ...props }) {
	return /* @__PURE__ */ jsx("div", {
		className: cn("animate-pulse rounded-md bg-primary/10", className),
		...props
	});
}
//#endregion
//#region src/components/ui/tooltip.tsx
var TooltipProvider = TooltipPrimitive.Provider;
var Tooltip = TooltipPrimitive.Root;
var TooltipTrigger = TooltipPrimitive.Trigger;
var TooltipContent = React.forwardRef(({ className, sideOffset = 4, ...props }, ref) => /* @__PURE__ */ jsx(TooltipPrimitive.Portal, { children: /* @__PURE__ */ jsx(TooltipPrimitive.Content, {
	ref,
	sideOffset,
	className: cn("z-50 overflow-hidden rounded-md bg-primary px-3 py-1.5 text-xs text-primary-foreground animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 origin-(--radix-tooltip-content-transform-origin)", className),
	...props
}) }));
TooltipContent.displayName = TooltipPrimitive.Content.displayName;
//#endregion
//#region src/components/ui/sidebar.tsx
var SIDEBAR_COOKIE_NAME = "sidebar_state";
var SIDEBAR_COOKIE_MAX_AGE = 604800;
var SIDEBAR_WIDTH = "16rem";
var SIDEBAR_WIDTH_MOBILE = "18rem";
var SIDEBAR_WIDTH_ICON = "3rem";
var SIDEBAR_KEYBOARD_SHORTCUT = "b";
var SidebarContext = React.createContext(null);
function useSidebar() {
	const context = React.useContext(SidebarContext);
	if (!context) throw new Error("useSidebar must be used within a SidebarProvider.");
	return context;
}
var SidebarProvider = React.forwardRef(({ defaultOpen = true, open: openProp, onOpenChange: setOpenProp, className, style, children, ...props }, ref) => {
	const isMobile = useIsMobile();
	const [openMobile, setOpenMobile] = React.useState(false);
	const [_open, _setOpen] = React.useState(defaultOpen);
	const open = openProp ?? _open;
	const setOpen = React.useCallback((value) => {
		const openState = typeof value === "function" ? value(open) : value;
		if (setOpenProp) setOpenProp(openState);
		else _setOpen(openState);
		document.cookie = `${SIDEBAR_COOKIE_NAME}=${openState}; path=/; max-age=${SIDEBAR_COOKIE_MAX_AGE}`;
	}, [setOpenProp, open]);
	const toggleSidebar = React.useCallback(() => {
		return isMobile ? setOpenMobile((open) => !open) : setOpen((open) => !open);
	}, [
		isMobile,
		setOpen,
		setOpenMobile
	]);
	React.useEffect(() => {
		const handleKeyDown = (event) => {
			if (event.key === SIDEBAR_KEYBOARD_SHORTCUT && (event.metaKey || event.ctrlKey)) {
				event.preventDefault();
				toggleSidebar();
			}
		};
		window.addEventListener("keydown", handleKeyDown);
		return () => window.removeEventListener("keydown", handleKeyDown);
	}, [toggleSidebar]);
	const state = open ? "expanded" : "collapsed";
	const contextValue = React.useMemo(() => ({
		state,
		open,
		setOpen,
		isMobile,
		openMobile,
		setOpenMobile,
		toggleSidebar
	}), [
		state,
		open,
		setOpen,
		isMobile,
		openMobile,
		setOpenMobile,
		toggleSidebar
	]);
	return /* @__PURE__ */ jsx(SidebarContext.Provider, {
		value: contextValue,
		children: /* @__PURE__ */ jsx(TooltipProvider, {
			delayDuration: 0,
			children: /* @__PURE__ */ jsx("div", {
				style: {
					"--sidebar-width": SIDEBAR_WIDTH,
					"--sidebar-width-icon": SIDEBAR_WIDTH_ICON,
					...style
				},
				className: cn("group/sidebar-wrapper flex min-h-svh w-full has-[[data-variant=inset]]:bg-sidebar", className),
				ref,
				...props,
				children
			})
		})
	});
});
SidebarProvider.displayName = "SidebarProvider";
var Sidebar = React.forwardRef(({ side = "left", variant = "sidebar", collapsible = "offcanvas", className, children, ...props }, ref) => {
	const { isMobile, state, openMobile, setOpenMobile } = useSidebar();
	if (collapsible === "none") return /* @__PURE__ */ jsx("div", {
		className: cn("flex h-full w-(--sidebar-width) flex-col bg-sidebar text-sidebar-foreground", className),
		ref,
		...props,
		children
	});
	if (isMobile) return /* @__PURE__ */ jsx(Sheet, {
		open: openMobile,
		onOpenChange: setOpenMobile,
		...props,
		children: /* @__PURE__ */ jsxs(SheetContent, {
			"data-sidebar": "sidebar",
			"data-mobile": "true",
			className: "w-(--sidebar-width) bg-sidebar p-0 text-sidebar-foreground [&>button]:hidden",
			style: { "--sidebar-width": SIDEBAR_WIDTH_MOBILE },
			side,
			children: [/* @__PURE__ */ jsxs(SheetHeader, {
				className: "sr-only",
				children: [/* @__PURE__ */ jsx(SheetTitle, { children: "Sidebar" }), /* @__PURE__ */ jsx(SheetDescription, { children: "Displays the mobile sidebar." })]
			}), /* @__PURE__ */ jsx("div", {
				className: "flex h-full w-full flex-col",
				children
			})]
		})
	});
	return /* @__PURE__ */ jsxs("div", {
		ref,
		className: "group peer hidden text-sidebar-foreground md:block",
		"data-state": state,
		"data-collapsible": state === "collapsed" ? collapsible : "",
		"data-variant": variant,
		"data-side": side,
		children: [/* @__PURE__ */ jsx("div", { className: cn("relative w-(--sidebar-width) bg-transparent transition-[width] duration-200 ease-linear", "group-data-[collapsible=offcanvas]:w-0", "group-data-[side=right]:rotate-180", variant === "floating" || variant === "inset" ? "group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)_+_theme(spacing.4))]" : "group-data-[collapsible=icon]:w-(--sidebar-width-icon)") }), /* @__PURE__ */ jsx("div", {
			className: cn("fixed inset-y-0 z-10 hidden h-svh w-(--sidebar-width) transition-[left,right,width] duration-200 ease-linear md:flex", side === "left" ? "left-0 group-data-[collapsible=offcanvas]:left-[calc(var(--sidebar-width)*-1)]" : "right-0 group-data-[collapsible=offcanvas]:right-[calc(var(--sidebar-width)*-1)]", variant === "floating" || variant === "inset" ? "p-2 group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)_+_theme(spacing.4)_+2px)]" : "group-data-[collapsible=icon]:w-(--sidebar-width-icon) group-data-[side=left]:border-r group-data-[side=right]:border-l", className),
			...props,
			children: /* @__PURE__ */ jsx("div", {
				"data-sidebar": "sidebar",
				className: "flex h-full w-full flex-col bg-sidebar group-data-[variant=floating]:rounded-lg group-data-[variant=floating]:border group-data-[variant=floating]:border-sidebar-border group-data-[variant=floating]:shadow",
				children
			})
		})]
	});
});
Sidebar.displayName = "Sidebar";
var SidebarTrigger = React.forwardRef(({ className, onClick, ...props }, ref) => {
	const { toggleSidebar } = useSidebar();
	return /* @__PURE__ */ jsxs(Button, {
		ref,
		"data-sidebar": "trigger",
		variant: "ghost",
		size: "icon",
		className: cn("h-7 w-7", className),
		onClick: (event) => {
			onClick?.(event);
			toggleSidebar();
		},
		...props,
		children: [/* @__PURE__ */ jsx(PanelLeft, {}), /* @__PURE__ */ jsx("span", {
			className: "sr-only",
			children: "Toggle Sidebar"
		})]
	});
});
SidebarTrigger.displayName = "SidebarTrigger";
var SidebarRail = React.forwardRef(({ className, ...props }, ref) => {
	const { toggleSidebar } = useSidebar();
	return /* @__PURE__ */ jsx("button", {
		ref,
		"data-sidebar": "rail",
		"aria-label": "Toggle Sidebar",
		tabIndex: -1,
		onClick: toggleSidebar,
		title: "Toggle Sidebar",
		className: cn("absolute inset-y-0 z-20 hidden w-4 -translate-x-1/2 transition-all ease-linear after:absolute after:inset-y-0 after:left-1/2 after:w-[2px] hover:after:bg-sidebar-border group-data-[side=left]:-right-4 group-data-[side=right]:left-0 sm:flex", "[[data-side=left]_&]:cursor-w-resize [[data-side=right]_&]:cursor-e-resize", "[[data-side=left][data-state=collapsed]_&]:cursor-e-resize [[data-side=right][data-state=collapsed]_&]:cursor-w-resize", "group-data-[collapsible=offcanvas]:translate-x-0 group-data-[collapsible=offcanvas]:after:left-full group-data-[collapsible=offcanvas]:hover:bg-sidebar", "[[data-side=left][data-collapsible=offcanvas]_&]:-right-2", "[[data-side=right][data-collapsible=offcanvas]_&]:-left-2", className),
		...props
	});
});
SidebarRail.displayName = "SidebarRail";
var SidebarInset = React.forwardRef(({ className, ...props }, ref) => {
	return /* @__PURE__ */ jsx("main", {
		ref,
		className: cn("relative flex w-full flex-1 flex-col bg-background", "md:peer-data-[variant=inset]:m-2 md:peer-data-[state=collapsed]:peer-data-[variant=inset]:ml-2 md:peer-data-[variant=inset]:ml-0 md:peer-data-[variant=inset]:rounded-xl md:peer-data-[variant=inset]:shadow", className),
		...props
	});
});
SidebarInset.displayName = "SidebarInset";
var SidebarInput = React.forwardRef(({ className, ...props }, ref) => {
	return /* @__PURE__ */ jsx(Input, {
		ref,
		"data-sidebar": "input",
		className: cn("h-8 w-full bg-background shadow-none focus-visible:ring-2 focus-visible:ring-sidebar-ring", className),
		...props
	});
});
SidebarInput.displayName = "SidebarInput";
var SidebarHeader = React.forwardRef(({ className, ...props }, ref) => {
	return /* @__PURE__ */ jsx("div", {
		ref,
		"data-sidebar": "header",
		className: cn("flex flex-col gap-2 p-2", className),
		...props
	});
});
SidebarHeader.displayName = "SidebarHeader";
var SidebarFooter = React.forwardRef(({ className, ...props }, ref) => {
	return /* @__PURE__ */ jsx("div", {
		ref,
		"data-sidebar": "footer",
		className: cn("flex flex-col gap-2 p-2", className),
		...props
	});
});
SidebarFooter.displayName = "SidebarFooter";
var SidebarSeparator = React.forwardRef(({ className, ...props }, ref) => {
	return /* @__PURE__ */ jsx(Separator, {
		ref,
		"data-sidebar": "separator",
		className: cn("mx-2 w-auto bg-sidebar-border", className),
		...props
	});
});
SidebarSeparator.displayName = "SidebarSeparator";
var SidebarContent = React.forwardRef(({ className, ...props }, ref) => {
	return /* @__PURE__ */ jsx("div", {
		ref,
		"data-sidebar": "content",
		className: cn("flex min-h-0 flex-1 flex-col gap-2 overflow-auto group-data-[collapsible=icon]:overflow-hidden", className),
		...props
	});
});
SidebarContent.displayName = "SidebarContent";
var SidebarGroup = React.forwardRef(({ className, ...props }, ref) => {
	return /* @__PURE__ */ jsx("div", {
		ref,
		"data-sidebar": "group",
		className: cn("relative flex w-full min-w-0 flex-col p-2", className),
		...props
	});
});
SidebarGroup.displayName = "SidebarGroup";
var SidebarGroupLabel = React.forwardRef(({ className, asChild = false, ...props }, ref) => {
	return /* @__PURE__ */ jsx(asChild ? Slot : "div", {
		ref,
		"data-sidebar": "group-label",
		className: cn("flex h-8 shrink-0 items-center rounded-md px-2 text-xs font-medium text-sidebar-foreground/70 outline-none ring-sidebar-ring transition-[margin,opacity] duration-200 ease-linear focus-visible:ring-2 [&>svg]:size-4 [&>svg]:shrink-0", "group-data-[collapsible=icon]:-mt-8 group-data-[collapsible=icon]:opacity-0", className),
		...props
	});
});
SidebarGroupLabel.displayName = "SidebarGroupLabel";
var SidebarGroupAction = React.forwardRef(({ className, asChild = false, ...props }, ref) => {
	return /* @__PURE__ */ jsx(asChild ? Slot : "button", {
		ref,
		"data-sidebar": "group-action",
		className: cn("absolute right-3 top-3.5 flex aspect-square w-5 items-center justify-center rounded-md p-0 text-sidebar-foreground outline-none ring-sidebar-ring cursor-pointer transition-transform hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 [&>svg]:size-4 [&>svg]:shrink-0", "after:absolute after:-inset-2 after:md:hidden", "group-data-[collapsible=icon]:hidden", className),
		...props
	});
});
SidebarGroupAction.displayName = "SidebarGroupAction";
var SidebarGroupContent = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("div", {
	ref,
	"data-sidebar": "group-content",
	className: cn("w-full text-sm", className),
	...props
}));
SidebarGroupContent.displayName = "SidebarGroupContent";
var SidebarMenu = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("ul", {
	ref,
	"data-sidebar": "menu",
	className: cn("flex w-full min-w-0 flex-col gap-1", className),
	...props
}));
SidebarMenu.displayName = "SidebarMenu";
var SidebarMenuItem = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("li", {
	ref,
	"data-sidebar": "menu-item",
	className: cn("group/menu-item relative", className),
	...props
}));
SidebarMenuItem.displayName = "SidebarMenuItem";
var sidebarMenuButtonVariants = cva("peer/menu-button flex w-full items-center gap-2 overflow-hidden rounded-md p-2 text-left text-sm outline-none ring-sidebar-ring cursor-pointer transition-[width,height,padding] hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 active:bg-sidebar-accent active:text-sidebar-accent-foreground disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed group-has-[[data-sidebar=menu-action]]/menu-item:pr-8 aria-disabled:pointer-events-none aria-disabled:opacity-50 data-[active=true]:bg-sidebar-accent data-[active=true]:font-medium data-[active=true]:text-sidebar-accent-foreground data-[state=open]:hover:bg-sidebar-accent data-[state=open]:hover:text-sidebar-accent-foreground group-data-[collapsible=icon]:!size-8 group-data-[collapsible=icon]:!p-2 [&>span:last-child]:truncate [&>svg]:size-4 [&>svg]:shrink-0", {
	variants: {
		variant: {
			default: "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
			outline: "bg-background shadow-[0_0_0_1px_var(--sidebar-border)] hover:bg-sidebar-accent hover:text-sidebar-accent-foreground hover:shadow-[0_0_0_1px_var(--sidebar-accent)]"
		},
		size: {
			default: "h-8 text-sm",
			sm: "h-7 text-xs",
			lg: "h-12 text-sm group-data-[collapsible=icon]:!p-0"
		}
	},
	defaultVariants: {
		variant: "default",
		size: "default"
	}
});
var SidebarMenuButton = React.forwardRef(({ asChild = false, isActive = false, variant = "default", size = "default", tooltip, className, ...props }, ref) => {
	const Comp = asChild ? Slot : "button";
	const { isMobile, state } = useSidebar();
	const button = /* @__PURE__ */ jsx(Comp, {
		ref,
		"data-sidebar": "menu-button",
		"data-size": size,
		"data-active": isActive,
		className: cn(sidebarMenuButtonVariants({
			variant,
			size
		}), className),
		...props
	});
	if (!tooltip) return button;
	if (typeof tooltip === "string") tooltip = { children: tooltip };
	return /* @__PURE__ */ jsxs(Tooltip, { children: [/* @__PURE__ */ jsx(TooltipTrigger, {
		asChild: true,
		children: button
	}), /* @__PURE__ */ jsx(TooltipContent, {
		side: "right",
		align: "center",
		hidden: state !== "collapsed" || isMobile,
		...tooltip
	})] });
});
SidebarMenuButton.displayName = "SidebarMenuButton";
var SidebarMenuAction = React.forwardRef(({ className, asChild = false, showOnHover = false, ...props }, ref) => {
	return /* @__PURE__ */ jsx(asChild ? Slot : "button", {
		ref,
		"data-sidebar": "menu-action",
		className: cn("absolute right-1 top-1.5 flex aspect-square w-5 items-center justify-center rounded-md p-0 text-sidebar-foreground outline-none ring-sidebar-ring cursor-pointer transition-transform hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 peer-hover/menu-button:text-sidebar-accent-foreground [&>svg]:size-4 [&>svg]:shrink-0", "after:absolute after:-inset-2 after:md:hidden", "peer-data-[size=sm]/menu-button:top-1", "peer-data-[size=default]/menu-button:top-1.5", "peer-data-[size=lg]/menu-button:top-2.5", "group-data-[collapsible=icon]:hidden", showOnHover && "group-focus-within/menu-item:opacity-100 group-hover/menu-item:opacity-100 data-[state=open]:opacity-100 peer-data-[active=true]/menu-button:text-sidebar-accent-foreground md:opacity-0", className),
		...props
	});
});
SidebarMenuAction.displayName = "SidebarMenuAction";
var SidebarMenuBadge = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("div", {
	ref,
	"data-sidebar": "menu-badge",
	className: cn("pointer-events-none absolute right-1 flex h-5 min-w-5 select-none items-center justify-center rounded-md px-1 text-xs font-medium tabular-nums text-sidebar-foreground", "peer-hover/menu-button:text-sidebar-accent-foreground peer-data-[active=true]/menu-button:text-sidebar-accent-foreground", "peer-data-[size=sm]/menu-button:top-1", "peer-data-[size=default]/menu-button:top-1.5", "peer-data-[size=lg]/menu-button:top-2.5", "group-data-[collapsible=icon]:hidden", className),
	...props
}));
SidebarMenuBadge.displayName = "SidebarMenuBadge";
var SidebarMenuSkeleton = React.forwardRef(({ className, showIcon = false, ...props }, ref) => {
	const width = React.useMemo(() => {
		return `${Math.floor(Math.random() * 40) + 50}%`;
	}, []);
	return /* @__PURE__ */ jsxs("div", {
		ref,
		"data-sidebar": "menu-skeleton",
		className: cn("flex h-8 items-center gap-2 rounded-md px-2", className),
		...props,
		children: [showIcon && /* @__PURE__ */ jsx(Skeleton, {
			className: "size-4 rounded-md",
			"data-sidebar": "menu-skeleton-icon"
		}), /* @__PURE__ */ jsx(Skeleton, {
			className: "h-4 max-w-(--skeleton-width) flex-1",
			"data-sidebar": "menu-skeleton-text",
			style: { "--skeleton-width": width }
		})]
	});
});
SidebarMenuSkeleton.displayName = "SidebarMenuSkeleton";
var SidebarMenuSub = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("ul", {
	ref,
	"data-sidebar": "menu-sub",
	className: cn("mx-3.5 flex min-w-0 translate-x-px flex-col gap-1 border-l border-sidebar-border px-2.5 py-0.5", "group-data-[collapsible=icon]:hidden", className),
	...props
}));
SidebarMenuSub.displayName = "SidebarMenuSub";
var SidebarMenuSubItem = React.forwardRef(({ ...props }, ref) => /* @__PURE__ */ jsx("li", {
	ref,
	...props
}));
SidebarMenuSubItem.displayName = "SidebarMenuSubItem";
var SidebarMenuSubButton = React.forwardRef(({ asChild = false, size = "md", isActive, className, ...props }, ref) => {
	return /* @__PURE__ */ jsx(asChild ? Slot : "a", {
		ref,
		"data-sidebar": "menu-sub-button",
		"data-size": size,
		"data-active": isActive,
		className: cn("flex h-7 min-w-0 -translate-x-px items-center gap-2 overflow-hidden rounded-md px-2 text-sidebar-foreground outline-none ring-sidebar-ring cursor-pointer hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 active:bg-sidebar-accent active:text-sidebar-accent-foreground disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed aria-disabled:pointer-events-none aria-disabled:opacity-50 [&>span:last-child]:truncate [&>svg]:size-4 [&>svg]:shrink-0 [&>svg]:text-sidebar-accent-foreground", "data-[active=true]:bg-sidebar-accent data-[active=true]:text-sidebar-accent-foreground", size === "sm" && "text-xs", size === "md" && "text-sm", "group-data-[collapsible=icon]:hidden", className),
		...props
	});
});
SidebarMenuSubButton.displayName = "SidebarMenuSubButton";
//#endregion
//#region src/components/ui/badge.tsx
var badgeVariants = cva("inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2", {
	variants: { variant: {
		default: "border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/80",
		secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
		destructive: "border-transparent bg-destructive text-destructive-foreground shadow hover:bg-destructive/80",
		outline: "text-foreground",
		success: "border-success/20 bg-success/12 text-success hover:bg-success/18 dark:border-success/30 dark:bg-success/18",
		warning: "border-warning/30 bg-warning/15 text-warning-foreground hover:bg-warning/20 dark:text-warning",
		info: "border-info/20 bg-info/12 text-info hover:bg-info/18 dark:border-info/30 dark:bg-info/18",
		pending: "border-warning/30 bg-warning/10 text-warning-foreground/90 hover:bg-warning/15 dark:text-warning",
		high: "border-destructive/20 bg-destructive/10 text-destructive hover:bg-destructive/15",
		low: "border-transparent bg-muted text-muted-foreground hover:bg-muted/80"
	} },
	defaultVariants: { variant: "default" }
});
function Badge({ className, variant, ...props }) {
	return /* @__PURE__ */ jsx("div", {
		className: cn(badgeVariants({ variant }), className),
		...props
	});
}
//#endregion
//#region src/components/layout/app-sidebar.tsx
var groups = [
	{
		label: "Overview",
		items: [{
			title: "Dashboard",
			url: "/",
			icon: LayoutDashboard
		}]
	},
	{
		label: "Pipeline",
		items: [
			{
				title: "Discovery",
				url: "/discovery",
				icon: Radar
			},
			{
				title: "Companies",
				url: "/companies",
				icon: Building2
			},
			{
				title: "Contacts",
				url: "/contacts",
				icon: Users
			},
			{
				title: "Research Queue",
				url: "/research-queue",
				icon: ClipboardList
			}
		]
	},
	{
		label: "Outreach",
		items: [
			{
				title: "Campaigns",
				url: "/campaigns",
				icon: Mail
			},
			{
				title: "Drafts",
				url: "/drafts",
				icon: FileText
			},
			{
				title: "Mailbox",
				url: "/mailbox",
				icon: Inbox
			}
		]
	},
	{
		label: "Insights",
		items: [{
			title: "Analytics",
			url: "/analytics",
			icon: BarChart3
		}, {
			title: "Reports",
			url: "/analytics",
			icon: FileBarChart,
			soon: true
		}]
	},
	{
		label: "System",
		items: [{
			title: "Settings",
			url: "/settings",
			icon: Settings
		}, {
			title: "Administration",
			url: "/settings",
			icon: ShieldCheck,
			soon: true
		}]
	}
];
function AppSidebar() {
	const pathname = useRouterState({ select: (s) => s.location.pathname });
	const isActive = (url) => url === "/" ? pathname === "/" : pathname.startsWith(url);
	return /* @__PURE__ */ jsxs(Sidebar, {
		collapsible: "icon",
		children: [
			/* @__PURE__ */ jsx(SidebarHeader, {
				className: "border-b border-sidebar-border",
				children: /* @__PURE__ */ jsxs(Link, {
					to: "/",
					className: "flex items-center gap-2.5 px-1.5 py-1.5",
					children: [/* @__PURE__ */ jsx("img", {
						src: "/yash-technology-logo.png",
						alt: "Yash Technology",
						className: "size-8 shrink-0 rounded-md object-contain"
					}), /* @__PURE__ */ jsxs("span", {
						className: "grid min-w-0 leading-tight group-data-[collapsible=icon]:hidden",
						children: [/* @__PURE__ */ jsx("span", {
							className: "truncate text-sm font-semibold text-sidebar-foreground",
							children: "Yash Technology"
						}), /* @__PURE__ */ jsx("span", {
							className: "truncate text-[11px] text-sidebar-foreground/60",
							children: "Outreach Hub"
						})]
					})]
				})
			}),
			/* @__PURE__ */ jsx(SidebarContent, { children: groups.map((group) => /* @__PURE__ */ jsxs(SidebarGroup, { children: [/* @__PURE__ */ jsx(SidebarGroupLabel, { children: group.label }), /* @__PURE__ */ jsx(SidebarGroupContent, { children: /* @__PURE__ */ jsx(SidebarMenu, { children: group.items.map((item) => /* @__PURE__ */ jsx(SidebarMenuItem, { children: /* @__PURE__ */ jsx(SidebarMenuButton, {
				asChild: true,
				isActive: isActive(item.url) && !("soon" in item),
				tooltip: item.title,
				children: /* @__PURE__ */ jsxs(Link, {
					to: item.url,
					className: "flex items-center gap-2",
					children: [
						/* @__PURE__ */ jsx(item.icon, { className: "size-4 shrink-0" }),
						/* @__PURE__ */ jsx("span", {
							className: "truncate",
							children: item.title
						}),
						"soon" in item ? /* @__PURE__ */ jsx(Badge, {
							variant: "outline",
							className: "ml-auto border-sidebar-border text-[10px] text-sidebar-foreground/60 group-data-[collapsible=icon]:hidden",
							children: "Soon"
						}) : null
					]
				})
			}) }, item.title)) }) })] }, group.label)) }),
			/* @__PURE__ */ jsx(SidebarFooter, {
				className: "border-t border-sidebar-border",
				children: /* @__PURE__ */ jsxs("div", {
					className: "flex items-center gap-2 px-1.5 py-1 text-[11px] text-sidebar-foreground/60 group-data-[collapsible=icon]:hidden",
					children: [/* @__PURE__ */ jsx("span", { className: "size-1.5 rounded-full bg-success" }), "Discovery engine online"]
				})
			})
		]
	});
}
//#endregion
//#region src/components/ui/breadcrumb.tsx
var Breadcrumb = React.forwardRef(({ ...props }, ref) => /* @__PURE__ */ jsx("nav", {
	ref,
	"aria-label": "breadcrumb",
	...props
}));
Breadcrumb.displayName = "Breadcrumb";
var BreadcrumbList = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("ol", {
	ref,
	className: cn("flex flex-wrap items-center gap-1.5 break-words text-sm text-muted-foreground sm:gap-2.5", className),
	...props
}));
BreadcrumbList.displayName = "BreadcrumbList";
var BreadcrumbItem = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("li", {
	ref,
	className: cn("inline-flex items-center gap-1.5", className),
	...props
}));
BreadcrumbItem.displayName = "BreadcrumbItem";
var BreadcrumbLink = React.forwardRef(({ asChild, className, ...props }, ref) => {
	return /* @__PURE__ */ jsx(asChild ? Slot : "a", {
		ref,
		className: cn("transition-colors hover:text-foreground", className),
		...props
	});
});
BreadcrumbLink.displayName = "BreadcrumbLink";
var BreadcrumbPage = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("span", {
	ref,
	role: "link",
	"aria-disabled": "true",
	"aria-current": "page",
	className: cn("font-normal text-foreground", className),
	...props
}));
BreadcrumbPage.displayName = "BreadcrumbPage";
var BreadcrumbSeparator = ({ children, className, ...props }) => /* @__PURE__ */ jsx("li", {
	role: "presentation",
	"aria-hidden": "true",
	className: cn("[&>svg]:w-3.5 [&>svg]:h-3.5", className),
	...props,
	children: children ?? /* @__PURE__ */ jsx(ChevronRight, {})
});
BreadcrumbSeparator.displayName = "BreadcrumbSeparator";
var BreadcrumbEllipsis = ({ className, ...props }) => /* @__PURE__ */ jsxs("span", {
	role: "presentation",
	"aria-hidden": "true",
	className: cn("flex h-9 w-9 items-center justify-center", className),
	...props,
	children: [/* @__PURE__ */ jsx(MoreHorizontal, { className: "h-4 w-4" }), /* @__PURE__ */ jsx("span", {
		className: "sr-only",
		children: "More"
	})]
});
BreadcrumbEllipsis.displayName = "BreadcrumbElipssis";
//#endregion
//#region src/components/ui/dialog.tsx
var Dialog = SheetPrimitive.Root;
var DialogPortal = SheetPrimitive.Portal;
var DialogOverlay = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(SheetPrimitive.Overlay, {
	ref,
	className: cn("fixed inset-0 z-50 bg-black/80  data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0", className),
	...props
}));
DialogOverlay.displayName = SheetPrimitive.Overlay.displayName;
var DialogContent = React.forwardRef(({ className, children, ...props }, ref) => /* @__PURE__ */ jsxs(DialogPortal, { children: [/* @__PURE__ */ jsx(DialogOverlay, {}), /* @__PURE__ */ jsxs(SheetPrimitive.Content, {
	ref,
	className: cn("fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 sm:rounded-lg", className),
	...props,
	children: [children, /* @__PURE__ */ jsxs(SheetPrimitive.Close, {
		className: "absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background cursor-pointer transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground",
		children: [/* @__PURE__ */ jsx(X, { className: "h-4 w-4" }), /* @__PURE__ */ jsx("span", {
			className: "sr-only",
			children: "Close"
		})]
	})]
})] }));
DialogContent.displayName = SheetPrimitive.Content.displayName;
var DialogHeader = ({ className, ...props }) => /* @__PURE__ */ jsx("div", {
	className: cn("flex flex-col space-y-1.5 text-center sm:text-left", className),
	...props
});
DialogHeader.displayName = "DialogHeader";
var DialogFooter = ({ className, ...props }) => /* @__PURE__ */ jsx("div", {
	className: cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2", className),
	...props
});
DialogFooter.displayName = "DialogFooter";
var DialogTitle = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(SheetPrimitive.Title, {
	ref,
	className: cn("text-lg font-semibold leading-none tracking-tight", className),
	...props
}));
DialogTitle.displayName = SheetPrimitive.Title.displayName;
var DialogDescription = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(SheetPrimitive.Description, {
	ref,
	className: cn("text-sm text-muted-foreground", className),
	...props
}));
DialogDescription.displayName = SheetPrimitive.Description.displayName;
//#endregion
//#region src/components/ui/command.tsx
var Command$1 = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(Command, {
	ref,
	className: cn("flex h-full w-full flex-col overflow-hidden rounded-md bg-popover text-popover-foreground", className),
	...props
}));
Command$1.displayName = Command.displayName;
var CommandDialog = ({ children, ...props }) => {
	return /* @__PURE__ */ jsx(Dialog, {
		...props,
		children: /* @__PURE__ */ jsx(DialogContent, {
			className: "overflow-hidden p-0",
			children: /* @__PURE__ */ jsx(Command$1, {
				className: "[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group]:not([hidden])_~[cmdk-group]]:pt-0 [&_[cmdk-group]]:px-2 [&_[cmdk-input-wrapper]_svg]:h-5 [&_[cmdk-input-wrapper]_svg]:w-5 [&_[cmdk-input]]:h-12 [&_[cmdk-item]]:px-2 [&_[cmdk-item]]:py-3 [&_[cmdk-item]_svg]:h-5 [&_[cmdk-item]_svg]:w-5",
				children
			})
		})
	});
};
var CommandInput = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxs("div", {
	className: "flex items-center border-b px-3",
	"cmdk-input-wrapper": "",
	children: [/* @__PURE__ */ jsx(Search, { className: "mr-2 h-4 w-4 shrink-0 opacity-50" }), /* @__PURE__ */ jsx(Command.Input, {
		ref,
		className: cn("flex h-10 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50", className),
		...props
	})]
}));
CommandInput.displayName = Command.Input.displayName;
var CommandList = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(Command.List, {
	ref,
	className: cn("max-h-[300px] overflow-y-auto overflow-x-hidden", className),
	...props
}));
CommandList.displayName = Command.List.displayName;
var CommandEmpty = React.forwardRef((props, ref) => /* @__PURE__ */ jsx(Command.Empty, {
	ref,
	className: "py-6 text-center text-sm",
	...props
}));
CommandEmpty.displayName = Command.Empty.displayName;
var CommandGroup = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(Command.Group, {
	ref,
	className: cn("overflow-hidden p-1 text-foreground [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground", className),
	...props
}));
CommandGroup.displayName = Command.Group.displayName;
var CommandSeparator = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(Command.Separator, {
	ref,
	className: cn("-mx-1 h-px bg-border", className),
	...props
}));
CommandSeparator.displayName = Command.Separator.displayName;
var CommandItem = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(Command.Item, {
	ref,
	className: cn("relative flex cursor-default gap-2 select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none data-[disabled=true]:pointer-events-none data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground data-[disabled=true]:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0", className),
	...props
}));
CommandItem.displayName = Command.Item.displayName;
var CommandShortcut = ({ className, ...props }) => {
	return /* @__PURE__ */ jsx("span", {
		className: cn("ml-auto text-xs tracking-widest text-muted-foreground", className),
		...props
	});
};
CommandShortcut.displayName = "CommandShortcut";
//#endregion
//#region src/components/ui/dropdown-menu.tsx
var DropdownMenu = DropdownMenuPrimitive.Root;
var DropdownMenuTrigger = DropdownMenuPrimitive.Trigger;
var DropdownMenuSubTrigger = React.forwardRef(({ className, inset, children, ...props }, ref) => /* @__PURE__ */ jsxs(DropdownMenuPrimitive.SubTrigger, {
	ref,
	className: cn("flex cursor-default select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none focus:bg-accent data-[state=open]:bg-accent [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0", inset && "pl-8", className),
	...props,
	children: [children, /* @__PURE__ */ jsx(ChevronRight, { className: "ml-auto" })]
}));
DropdownMenuSubTrigger.displayName = DropdownMenuPrimitive.SubTrigger.displayName;
var DropdownMenuSubContent = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(DropdownMenuPrimitive.SubContent, {
	ref,
	className: cn("z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-lg data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 origin-(--radix-dropdown-menu-content-transform-origin)", className),
	...props
}));
DropdownMenuSubContent.displayName = DropdownMenuPrimitive.SubContent.displayName;
var DropdownMenuContent = React.forwardRef(({ className, sideOffset = 4, ...props }, ref) => /* @__PURE__ */ jsx(DropdownMenuPrimitive.Portal, { children: /* @__PURE__ */ jsx(DropdownMenuPrimitive.Content, {
	ref,
	sideOffset,
	className: cn("z-50 max-h-[var(--radix-dropdown-menu-content-available-height)] min-w-[8rem] overflow-y-auto overflow-x-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md", "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 origin-(--radix-dropdown-menu-content-transform-origin)", className),
	...props
}) }));
DropdownMenuContent.displayName = DropdownMenuPrimitive.Content.displayName;
var DropdownMenuItem = React.forwardRef(({ className, inset, ...props }, ref) => /* @__PURE__ */ jsx(DropdownMenuPrimitive.Item, {
	ref,
	className: cn("relative flex cursor-default select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&>svg]:size-4 [&>svg]:shrink-0", inset && "pl-8", className),
	...props
}));
DropdownMenuItem.displayName = DropdownMenuPrimitive.Item.displayName;
var DropdownMenuCheckboxItem = React.forwardRef(({ className, children, ...props }, ref) => /* @__PURE__ */ jsxs(DropdownMenuPrimitive.CheckboxItem, {
	ref,
	className: cn("relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50", className),
	...props,
	children: [/* @__PURE__ */ jsx("span", {
		className: "absolute left-2 flex h-3.5 w-3.5 items-center justify-center",
		children: /* @__PURE__ */ jsx(DropdownMenuPrimitive.ItemIndicator, { children: /* @__PURE__ */ jsx(Check, { className: "h-4 w-4" }) })
	}), children]
}));
DropdownMenuCheckboxItem.displayName = DropdownMenuPrimitive.CheckboxItem.displayName;
var DropdownMenuRadioItem = React.forwardRef(({ className, children, ...props }, ref) => /* @__PURE__ */ jsxs(DropdownMenuPrimitive.RadioItem, {
	ref,
	className: cn("relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50", className),
	...props,
	children: [/* @__PURE__ */ jsx("span", {
		className: "absolute left-2 flex h-3.5 w-3.5 items-center justify-center",
		children: /* @__PURE__ */ jsx(DropdownMenuPrimitive.ItemIndicator, { children: /* @__PURE__ */ jsx(Circle, { className: "h-2 w-2 fill-current" }) })
	}), children]
}));
DropdownMenuRadioItem.displayName = DropdownMenuPrimitive.RadioItem.displayName;
var DropdownMenuLabel = React.forwardRef(({ className, inset, ...props }, ref) => /* @__PURE__ */ jsx(DropdownMenuPrimitive.Label, {
	ref,
	className: cn("px-2 py-1.5 text-sm font-semibold", inset && "pl-8", className),
	...props
}));
DropdownMenuLabel.displayName = DropdownMenuPrimitive.Label.displayName;
var DropdownMenuSeparator = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(DropdownMenuPrimitive.Separator, {
	ref,
	className: cn("-mx-1 my-1 h-px bg-muted", className),
	...props
}));
DropdownMenuSeparator.displayName = DropdownMenuPrimitive.Separator.displayName;
var DropdownMenuShortcut = ({ className, ...props }) => {
	return /* @__PURE__ */ jsx("span", {
		className: cn("ml-auto text-xs tracking-widest opacity-60", className),
		...props
	});
};
DropdownMenuShortcut.displayName = "DropdownMenuShortcut";
//#endregion
//#region src/components/ui/popover.tsx
var Popover = PopoverPrimitive.Root;
var PopoverTrigger = PopoverPrimitive.Trigger;
var PopoverContent = React.forwardRef(({ className, align = "center", sideOffset = 4, ...props }, ref) => /* @__PURE__ */ jsx(PopoverPrimitive.Portal, { children: /* @__PURE__ */ jsx(PopoverPrimitive.Content, {
	ref,
	align,
	sideOffset,
	className: cn("z-50 w-72 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 origin-(--radix-popover-content-transform-origin)", className),
	...props
}) }));
PopoverContent.displayName = PopoverPrimitive.Content.displayName;
//#endregion
//#region src/components/ui/avatar.tsx
var Avatar = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(AvatarPrimitive.Root, {
	ref,
	className: cn("relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full", className),
	...props
}));
Avatar.displayName = AvatarPrimitive.Root.displayName;
var AvatarImage = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(AvatarPrimitive.Image, {
	ref,
	className: cn("aspect-square h-full w-full", className),
	...props
}));
AvatarImage.displayName = AvatarPrimitive.Image.displayName;
var AvatarFallback = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(AvatarPrimitive.Fallback, {
	ref,
	className: cn("flex h-full w-full items-center justify-center rounded-full bg-muted", className),
	...props
}));
AvatarFallback.displayName = AvatarPrimitive.Fallback.displayName;
//#endregion
//#region src/components/layout/topbar.tsx
var LABELS = {
	discovery: "Discovery",
	companies: "Companies",
	contacts: "Contacts",
	"research-queue": "Research Queue",
	campaigns: "Campaigns",
	drafts: "Drafts",
	mailbox: "Mailbox",
	analytics: "Analytics",
	reports: "Reports",
	settings: "Settings"
};
var NOTIFICATIONS = [
	{
		id: "n1",
		title: "Reply received",
		body: "Priya Iyer · Meridian Pharma Labs",
		time: "6m"
	},
	{
		id: "n2",
		title: "Campaign needs approval",
		body: "Warehouse Racking — 3PL Wave 2",
		time: "1h"
	},
	{
		id: "n3",
		title: "Discovery run finished",
		body: "63 companies · GFRP Rebar",
		time: "3h"
	}
];
function Topbar() {
	const pathname = useRouterState({ select: (s) => s.location.pathname });
	const { theme, toggle } = useTheme();
	const [open, setOpen] = useState(false);
	const navigate = useNavigate();
	const companies = useCompanies();
	const contacts = useContacts();
	const workspaceProfile = useWorkspaceProfile();
	const companyResults = companies.data ?? [];
	const contactResults = contacts.data ?? [];
	const profile = workspaceProfile.data;
	const userName = profile?.user_name ?? "Company user";
	const userInitials = userName.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase() ?? "").join("") || "CU";
	useEffect(() => {
		const onKey = (e) => {
			if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
				e.preventDefault();
				setOpen((v) => !v);
			}
		};
		window.addEventListener("keydown", onKey);
		return () => window.removeEventListener("keydown", onKey);
	}, []);
	const crumbs = useMemo(() => {
		const parts = pathname.split("/").filter(Boolean);
		return parts.map((part, i) => ({
			label: LABELS[part] ?? part.replace(/_/g, " "),
			href: "/" + parts.slice(0, i + 1).join("/"),
			last: i === parts.length - 1
		}));
	}, [pathname]);
	return /* @__PURE__ */ jsxs("header", {
		className: "sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background/85 px-3 backdrop-blur md:px-5",
		children: [
			/* @__PURE__ */ jsx(SidebarTrigger, { className: "shrink-0" }),
			/* @__PURE__ */ jsx(Separator, {
				orientation: "vertical",
				className: "hidden h-5 md:block"
			}),
			/* @__PURE__ */ jsx(Breadcrumb, {
				className: "hidden min-w-0 md:block",
				children: /* @__PURE__ */ jsxs(BreadcrumbList, { children: [/* @__PURE__ */ jsx(BreadcrumbItem, { children: crumbs.length === 0 ? /* @__PURE__ */ jsx(BreadcrumbPage, { children: "Dashboard" }) : /* @__PURE__ */ jsx(BreadcrumbLink, {
					asChild: true,
					children: /* @__PURE__ */ jsx(Link, {
						to: "/",
						children: "Dashboard"
					})
				}) }), crumbs.map((c) => /* @__PURE__ */ jsxs("span", {
					className: "flex items-center gap-1.5",
					children: [/* @__PURE__ */ jsx(BreadcrumbSeparator, {}), /* @__PURE__ */ jsx(BreadcrumbItem, { children: c.last ? /* @__PURE__ */ jsx(BreadcrumbPage, {
						className: "max-w-[220px] truncate capitalize",
						children: c.label
					}) : /* @__PURE__ */ jsx(BreadcrumbLink, {
						className: "capitalize",
						href: c.href,
						children: c.label
					}) })]
				}, c.href))] })
			}),
			/* @__PURE__ */ jsxs("button", {
				onClick: () => setOpen(true),
				className: "ml-auto flex h-9 min-w-0 flex-1 items-center gap-2 rounded-md border bg-muted/40 px-3 text-sm text-muted-foreground transition-colors hover:bg-muted md:max-w-sm md:flex-none",
				children: [
					/* @__PURE__ */ jsx(Search, { className: "size-4 shrink-0" }),
					/* @__PURE__ */ jsx("span", {
						className: "truncate",
						children: "Search companies, contacts…"
					}),
					/* @__PURE__ */ jsx("kbd", {
						className: "ml-auto hidden shrink-0 rounded border bg-background px-1.5 py-0.5 text-[10px] font-medium md:inline",
						children: "⌘K"
					})
				]
			}),
			/* @__PURE__ */ jsxs(Popover, { children: [/* @__PURE__ */ jsx(PopoverTrigger, {
				asChild: true,
				children: /* @__PURE__ */ jsxs(Button, {
					variant: "ghost",
					size: "icon",
					className: "relative shrink-0",
					children: [/* @__PURE__ */ jsx(Bell, { className: "size-4" }), /* @__PURE__ */ jsx("span", { className: "absolute right-1.5 top-1.5 size-2 rounded-full bg-primary ring-2 ring-background" })]
				})
			}), /* @__PURE__ */ jsxs(PopoverContent, {
				align: "end",
				className: "w-80 p-0",
				children: [/* @__PURE__ */ jsxs("div", {
					className: "flex items-center justify-between border-b px-3 py-2",
					children: [/* @__PURE__ */ jsx("span", {
						className: "text-sm font-semibold",
						children: "Notifications"
					}), /* @__PURE__ */ jsxs(Button, {
						variant: "ghost",
						size: "sm",
						className: "h-7 gap-1 text-xs",
						children: [/* @__PURE__ */ jsx(Check, { className: "size-3" }), " Mark all read"]
					})]
				}), /* @__PURE__ */ jsx("div", {
					className: "divide-y",
					children: NOTIFICATIONS.map((n) => /* @__PURE__ */ jsxs("div", {
						className: "px-3 py-2.5 hover:bg-muted/50",
						children: [/* @__PURE__ */ jsxs("div", {
							className: "flex items-center justify-between gap-2",
							children: [/* @__PURE__ */ jsx("p", {
								className: "truncate text-sm font-medium",
								children: n.title
							}), /* @__PURE__ */ jsx("span", {
								className: "shrink-0 text-[11px] text-muted-foreground",
								children: n.time
							})]
						}), /* @__PURE__ */ jsx("p", {
							className: "truncate text-xs text-muted-foreground",
							children: n.body
						})]
					}, n.id))
				})]
			})] }),
			/* @__PURE__ */ jsx(Button, {
				variant: "ghost",
				size: "icon",
				onClick: toggle,
				className: "shrink-0",
				"aria-label": "Toggle theme",
				children: theme === "dark" ? /* @__PURE__ */ jsx(Sun, { className: "size-4" }) : /* @__PURE__ */ jsx(Moon, { className: "size-4" })
			}),
			/* @__PURE__ */ jsxs(DropdownMenu, { children: [/* @__PURE__ */ jsx(DropdownMenuTrigger, {
				asChild: true,
				children: /* @__PURE__ */ jsxs(Button, {
					variant: "ghost",
					className: "h-9 shrink-0 gap-2 px-1.5",
					children: [
						/* @__PURE__ */ jsx(Avatar, {
							className: "size-7",
							children: /* @__PURE__ */ jsx(AvatarFallback, {
								className: "bg-primary/10 text-xs font-semibold text-primary",
								children: userInitials
							})
						}),
						/* @__PURE__ */ jsx("span", {
							className: "hidden text-sm font-medium lg:inline",
							children: userName
						}),
						/* @__PURE__ */ jsx(ChevronsUpDown, { className: "hidden size-3.5 text-muted-foreground lg:inline" })
					]
				})
			}), /* @__PURE__ */ jsxs(DropdownMenuContent, {
				align: "end",
				className: "w-56",
				children: [
					/* @__PURE__ */ jsxs(DropdownMenuLabel, {
						className: "grid",
						children: [
							/* @__PURE__ */ jsx("span", {
								className: "text-sm",
								children: userName
							}),
							/* @__PURE__ */ jsx("span", {
								className: "hidden text-xs font-normal text-muted-foreground",
								children: "Sales Lead · Yash Technology"
							}),
							/* @__PURE__ */ jsxs("span", {
								className: "text-xs font-normal text-muted-foreground",
								children: [
									profile?.user_role ?? "Sales",
									" · ",
									profile?.company_name ?? "Yash Technology"
								]
							})
						]
					}),
					/* @__PURE__ */ jsx(DropdownMenuSeparator, {}),
					/* @__PURE__ */ jsxs(DropdownMenuItem, {
						disabled: true,
						className: "gap-2",
						children: [
							/* @__PURE__ */ jsx(Building, { className: "size-4" }),
							" Workspace: Yash HQ",
							/* @__PURE__ */ jsx(Badge, {
								variant: "outline",
								className: "ml-auto text-[10px]",
								children: "Soon"
							})
						]
					}),
					/* @__PURE__ */ jsxs(DropdownMenuItem, {
						className: "gap-2",
						children: [/* @__PURE__ */ jsx(User, { className: "size-4" }), " Profile"]
					}),
					/* @__PURE__ */ jsxs(DropdownMenuItem, {
						className: "gap-2",
						onSelect: () => navigate({ to: "/settings" }),
						children: [/* @__PURE__ */ jsx(Building, { className: "size-4" }), " Settings"]
					}),
					/* @__PURE__ */ jsx(DropdownMenuSeparator, {}),
					/* @__PURE__ */ jsxs(DropdownMenuItem, {
						className: "gap-2 text-destructive",
						children: [/* @__PURE__ */ jsx(LogOut, { className: "size-4" }), " Sign out"]
					})
				]
			})] }),
			/* @__PURE__ */ jsxs(CommandDialog, {
				open,
				onOpenChange: setOpen,
				children: [/* @__PURE__ */ jsx(CommandInput, { placeholder: "Search companies, contacts, campaigns…" }), /* @__PURE__ */ jsxs(CommandList, { children: [
					/* @__PURE__ */ jsx(CommandEmpty, { children: "No results found." }),
					/* @__PURE__ */ jsx(CommandGroup, {
						heading: "Companies",
						children: companyResults.slice(0, 6).map((c) => /* @__PURE__ */ jsxs(CommandItem, {
							value: c.name,
							onSelect: () => {
								setOpen(false);
								navigate({
									to: "/companies/$companyId",
									params: { companyId: String(c.id) }
								});
							},
							children: [
								/* @__PURE__ */ jsx(Building, { className: "size-4" }),
								/* @__PURE__ */ jsx("span", {
									className: "truncate",
									children: c.name
								}),
								/* @__PURE__ */ jsx("span", {
									className: "ml-auto text-xs text-muted-foreground",
									children: c.industry
								})
							]
						}, c.id))
					}),
					/* @__PURE__ */ jsx(CommandGroup, {
						heading: "Contacts",
						children: contactResults.slice(0, 6).map((c) => /* @__PURE__ */ jsxs(CommandItem, {
							value: `${c.name} ${c.company_name}`,
							onSelect: () => {
								setOpen(false);
								navigate({
									to: "/contacts/$contactId",
									params: { contactId: String(c.id) }
								});
							},
							children: [
								/* @__PURE__ */ jsx(User, { className: "size-4" }),
								/* @__PURE__ */ jsx("span", {
									className: "truncate",
									children: c.name
								}),
								/* @__PURE__ */ jsx("span", {
									className: "ml-auto text-xs text-muted-foreground",
									children: c.company_name
								})
							]
						}, c.id))
					})
				] })]
			})
		]
	});
}
//#endregion
//#region src/components/ui/sonner.tsx
var Toaster$1 = ({ ...props }) => {
	return /* @__PURE__ */ jsx(Toaster, {
		className: "toaster group",
		toastOptions: { classNames: {
			toast: "group toast group-[.toaster]:bg-background group-[.toaster]:text-foreground group-[.toaster]:border-border group-[.toaster]:shadow-lg",
			description: "group-[.toast]:text-muted-foreground",
			actionButton: "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground",
			cancelButton: "group-[.toast]:bg-muted group-[.toast]:text-muted-foreground"
		} },
		...props
	});
};
//#endregion
//#region src/routes/__root.tsx
function NotFoundComponent() {
	return /* @__PURE__ */ jsx("div", {
		className: "flex min-h-[60vh] items-center justify-center px-4",
		children: /* @__PURE__ */ jsxs("div", {
			className: "max-w-md text-center",
			children: [
				/* @__PURE__ */ jsx("h1", {
					className: "text-6xl font-bold text-foreground",
					children: "404"
				}),
				/* @__PURE__ */ jsx("h2", {
					className: "mt-3 text-lg font-semibold",
					children: "Page not found"
				}),
				/* @__PURE__ */ jsx("p", {
					className: "mt-2 text-sm text-muted-foreground",
					children: "This module doesn't exist in the Outreach Hub yet."
				}),
				/* @__PURE__ */ jsx("div", {
					className: "mt-6",
					children: /* @__PURE__ */ jsx(Link, {
						to: "/",
						className: "inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90",
						children: "Back to dashboard"
					})
				})
			]
		})
	});
}
function ErrorComponent({ error, reset }) {
	console.error(error);
	const router = useRouter();
	useEffect(() => {
		reportLovableError(error, { boundary: "tanstack_root_error_component" });
	}, [error]);
	return /* @__PURE__ */ jsx("div", {
		className: "flex min-h-[60vh] items-center justify-center px-4",
		children: /* @__PURE__ */ jsxs("div", {
			className: "max-w-md text-center",
			children: [
				/* @__PURE__ */ jsx("h1", {
					className: "text-xl font-semibold tracking-tight",
					children: "This page didn't load"
				}),
				/* @__PURE__ */ jsx("p", {
					className: "mt-2 text-sm text-muted-foreground",
					children: "Something went wrong. Try again or head back to the dashboard."
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "mt-6 flex flex-wrap justify-center gap-2",
					children: [/* @__PURE__ */ jsx("button", {
						onClick: () => {
							router.invalidate();
							reset();
						},
						className: "inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90",
						children: "Try again"
					}), /* @__PURE__ */ jsx("a", {
						href: "/",
						className: "inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent",
						children: "Go home"
					})]
				})
			]
		})
	});
}
var Route$12 = createRootRouteWithContext()({
	head: () => ({
		meta: [
			{ charSet: "utf-8" },
			{
				name: "viewport",
				content: "width=device-width, initial-scale=1"
			},
			{ title: "Yash Technology Outreach Hub" },
			{
				name: "description",
				content: "AI-powered B2B lead discovery, CRM and outreach platform for Yash Technology sales teams."
			},
			{
				property: "og:type",
				content: "website"
			},
			{
				name: "twitter:card",
				content: "summary_large_image"
			}
		],
		links: [
			{
				rel: "stylesheet",
				href: styles_default
			},
			{
				rel: "preconnect",
				href: "https://fonts.googleapis.com"
			},
			{
				rel: "preconnect",
				href: "https://fonts.gstatic.com",
				crossOrigin: "anonymous"
			},
			{
				rel: "stylesheet",
				href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Inter+Tight:wght@500;600;700&display=swap"
			},
			{
				rel: "icon",
				href: "/yash-technology-logo.png",
				type: "image/png"
			}
		]
	}),
	shellComponent: RootShell,
	component: RootComponent,
	notFoundComponent: NotFoundComponent,
	errorComponent: ErrorComponent
});
function RootShell({ children }) {
	return /* @__PURE__ */ jsxs("html", {
		lang: "en",
		children: [/* @__PURE__ */ jsx("head", { children: /* @__PURE__ */ jsx(HeadContent, {}) }), /* @__PURE__ */ jsxs("body", { children: [children, /* @__PURE__ */ jsx(Scripts, {})] })]
	});
}
function RootComponent() {
	const { queryClient } = Route$12.useRouteContext();
	return /* @__PURE__ */ jsx(QueryClientProvider, {
		client: queryClient,
		children: /* @__PURE__ */ jsx(ThemeProvider, { children: /* @__PURE__ */ jsxs(SidebarProvider, { children: [/* @__PURE__ */ jsxs("div", {
			className: "flex min-h-screen w-full",
			children: [/* @__PURE__ */ jsx(AppSidebar, {}), /* @__PURE__ */ jsxs(SidebarInset, {
				className: "min-w-0",
				children: [/* @__PURE__ */ jsx(Topbar, {}), /* @__PURE__ */ jsx("main", {
					className: "min-w-0 flex-1 space-y-5 p-4 md:p-6",
					children: /* @__PURE__ */ jsx(Outlet, {})
				})]
			})]
		}), /* @__PURE__ */ jsx(Toaster$1, {
			position: "top-right",
			richColors: true
		})] }) })
	});
}
//#endregion
//#region src/routes/index.tsx
var $$splitComponentImporter$11 = () => import("./routes-CUBAFU2l.js");
var Route$11 = createFileRoute("/")({
	head: () => ({ meta: [
		{ title: "Dashboard — Yash Technology Outreach Hub" },
		{
			name: "description",
			content: "Executive view of lead discovery, qualified pipeline, campaign performance and replies for Yash Technology sales teams."
		},
		{
			property: "og:title",
			content: "Dashboard — Yash Technology Outreach Hub"
		},
		{
			property: "og:description",
			content: "Discovery, CRM, outreach and pipeline metrics in one executive dashboard."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter$11, "component")
});
//#endregion
//#region src/routes/analytics.tsx
var $$splitComponentImporter$10 = () => import("./analytics-BwprI7kC.js");
var Route$10 = createFileRoute("/analytics")({
	head: () => ({ meta: [
		{ title: "Analytics — Yash Technology Outreach Hub" },
		{
			name: "description",
			content: "Reporting on discovery, outreach, replies and product target progress from FastAPI."
		},
		{
			property: "og:title",
			content: "Analytics — Yash Technology Outreach Hub"
		},
		{
			property: "og:description",
			content: "Reporting on discovery and outreach metrics across divisions."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter$10, "component")
});
//#endregion
//#region src/routes/campaigns.tsx
var $$splitComponentImporter$9 = () => import("./campaigns-BDhoBxGZ.js");
var Route$9 = createFileRoute("/campaigns")({
	head: () => ({ meta: [
		{ title: "Campaigns — Yash Technology Outreach Hub" },
		{
			name: "description",
			content: "Outreach campaigns with notes, owning company and linked message count."
		},
		{
			property: "og:title",
			content: "Campaigns — Yash Technology Outreach Hub"
		},
		{
			property: "og:description",
			content: "Manage outreach campaigns and their linked messages."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter$9, "component")
});
//#endregion
//#region src/routes/companies.tsx
var $$splitComponentImporter$8 = () => import("./companies-BhVBUV5V.js");
var Route$8 = createFileRoute("/companies")({
	head: () => ({ meta: [
		{ title: "Companies — Yash Technology Outreach Hub" },
		{
			name: "description",
			content: "CRM view of discovered companies with source, product fits, sync status and review flags."
		},
		{
			property: "og:title",
			content: "Companies — Yash Technology Outreach Hub"
		},
		{
			property: "og:description",
			content: "Filter, review and assign discovered companies across the CRM."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter$8, "component")
});
//#endregion
//#region src/routes/contacts.tsx
var $$splitComponentImporter$7 = () => import("./contacts-Deoejuow.js");
var Route$7 = createFileRoute("/contacts")({
	head: () => ({ meta: [
		{ title: "Contacts — Yash Technology Outreach Hub" },
		{
			name: "description",
			content: "Decision-maker directory with title, company, email, phone, verification status and primary contact flags."
		},
		{
			property: "og:title",
			content: "Contacts — Yash Technology Outreach Hub"
		},
		{
			property: "og:description",
			content: "Discovered contacts with contactability and review metadata."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter$7, "component")
});
//#endregion
//#region src/routes/discovery.tsx
var $$splitComponentImporter$6 = () => import("./discovery-DK2otFSX.js");
var Route$6 = createFileRoute("/discovery")({
	head: () => ({ meta: [
		{ title: "Discovery — Yash Technology Outreach Hub" },
		{
			name: "description",
			content: "Run Apollo-powered company and decision-maker discovery by backend profile and geography."
		},
		{
			property: "og:title",
			content: "Discovery — Yash Technology Outreach Hub"
		},
		{
			property: "og:description",
			content: "Launch discovery runs and monitor API usage, credits and search diagnostics."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter$6, "component")
});
//#endregion
//#region src/routes/drafts.tsx
var $$splitComponentImporter$5 = () => import("./drafts-CYaZ5BHv.js");
var Route$5 = createFileRoute("/drafts")({
	head: () => ({ meta: [
		{ title: "AI Drafts — Yash Technology Outreach Hub" },
		{
			name: "description",
			content: "Review, edit and save AI-generated outreach emails before they are scheduled."
		},
		{
			property: "og:title",
			content: "AI Drafts — Yash Technology Outreach Hub"
		},
		{
			property: "og:description",
			content: "Human-in-the-loop approval for outbound email drafts."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter$5, "component")
});
//#endregion
//#region src/routes/mailbox.tsx
var $$splitComponentImporter$4 = () => import("./mailbox-Bz_M-nA_.js");
var Route$4 = createFileRoute("/mailbox")({
	head: () => ({ meta: [
		{ title: "Mailbox — Yash Technology Outreach Hub" },
		{
			name: "description",
			content: "Sent, drafted, replied and bounced outreach messages from FastAPI."
		},
		{
			property: "og:title",
			content: "Mailbox — Yash Technology Outreach Hub"
		},
		{
			property: "og:description",
			content: "Track every outreach email and reply across connected mailboxes."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter$4, "component")
});
//#endregion
//#region src/routes/research-queue.tsx
var $$splitComponentImporter$3 = () => import("./research-queue-CRUth9KC.js");
var Route$3 = createFileRoute("/research-queue")({
	head: () => ({ meta: [
		{ title: "Research Queue — Yash Technology Outreach Hub" },
		{
			name: "description",
			content: "Manual review queue for discovery records requiring follow-up."
		},
		{
			property: "og:title",
			content: "Research Queue — Yash Technology Outreach Hub"
		},
		{
			property: "og:description",
			content: "Discovery records routed for manual review and remediation."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter$3, "component")
});
//#endregion
//#region src/routes/settings.tsx
var $$splitComponentImporter$2 = () => import("./settings-CIfBGT7U.js");
var Route$2 = createFileRoute("/settings")({
	head: () => ({ meta: [
		{ title: "Settings — Yash Technology Outreach Hub" },
		{
			name: "description",
			content: "Workspace settings, SMTP settings and daily lead targets."
		},
		{
			property: "og:title",
			content: "Settings — Yash Technology Outreach Hub"
		},
		{
			property: "og:description",
			content: "Configure workspace settings and product-level daily targets."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter$2, "component")
});
//#endregion
//#region src/routes/companies.$companyId.tsx
var $$splitComponentImporter$1 = () => import("./companies._companyId-BwhNGJfC.js");
var Route$1 = createFileRoute("/companies/$companyId")({
	head: () => ({ meta: [
		{ title: "Company record — Yash Technology Outreach Hub" },
		{
			name: "description",
			content: "Full company record with CRM source metadata and product fits."
		},
		{
			property: "og:title",
			content: "Company record — Yash Technology Outreach Hub"
		},
		{
			property: "og:description",
			content: "Company details, review flags and discovery source metadata."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter$1, "component")
});
//#endregion
//#region src/routes/contacts.$contactId.tsx
var $$splitComponentImporter = () => import("./contacts._contactId-B-kspQlH.js");
var Route = createFileRoute("/contacts/$contactId")({
	head: () => ({ meta: [
		{ title: "Contact profile — Yash Technology Outreach Hub" },
		{
			name: "description",
			content: "Decision-maker profile with messages, replies and contactability data."
		},
		{
			property: "og:title",
			content: "Contact profile — Yash Technology Outreach Hub"
		},
		{
			property: "og:description",
			content: "Contactability, outreach history and decision-maker metadata."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter, "component")
});
//#endregion
//#region src/routeTree.gen.ts
var IndexRoute = Route$11.update({
	id: "/",
	path: "/",
	getParentRoute: () => Route$12
});
var AnalyticsRoute = Route$10.update({
	id: "/analytics",
	path: "/analytics",
	getParentRoute: () => Route$12
});
var CampaignsRoute = Route$9.update({
	id: "/campaigns",
	path: "/campaigns",
	getParentRoute: () => Route$12
});
var CompaniesRoute = Route$8.update({
	id: "/companies",
	path: "/companies",
	getParentRoute: () => Route$12
});
var ContactsRoute = Route$7.update({
	id: "/contacts",
	path: "/contacts",
	getParentRoute: () => Route$12
});
var DiscoveryRoute = Route$6.update({
	id: "/discovery",
	path: "/discovery",
	getParentRoute: () => Route$12
});
var DraftsRoute = Route$5.update({
	id: "/drafts",
	path: "/drafts",
	getParentRoute: () => Route$12
});
var MailboxRoute = Route$4.update({
	id: "/mailbox",
	path: "/mailbox",
	getParentRoute: () => Route$12
});
var ResearchQueueRoute = Route$3.update({
	id: "/research-queue",
	path: "/research-queue",
	getParentRoute: () => Route$12
});
var SettingsRoute = Route$2.update({
	id: "/settings",
	path: "/settings",
	getParentRoute: () => Route$12
});
var CompaniesCompanyIdRoute = Route$1.update({
	id: "/$companyId",
	path: "/$companyId",
	getParentRoute: () => CompaniesRoute
});
var ContactsContactIdRoute = Route.update({
	id: "/$contactId",
	path: "/$contactId",
	getParentRoute: () => ContactsRoute
});
var CompaniesRouteChildren = { CompaniesCompanyIdRoute };
var CompaniesRouteWithChildren = CompaniesRoute._addFileChildren(CompaniesRouteChildren);
var ContactsRouteChildren = { ContactsContactIdRoute };
var rootRouteChildren = {
	IndexRoute,
	AnalyticsRoute,
	CampaignsRoute,
	CompaniesRoute: CompaniesRouteWithChildren,
	ContactsRoute: ContactsRoute._addFileChildren(ContactsRouteChildren),
	DiscoveryRoute,
	DraftsRoute,
	MailboxRoute,
	ResearchQueueRoute,
	SettingsRoute
};
var routeTree = Route$12._addFileChildren(rootRouteChildren)._addFileTypes();
//#endregion
//#region src/router.tsx
var router_exports = /* @__PURE__ */ __exportAll({ getRouter: () => getRouter });
var getRouter = () => {
	const queryClient = new QueryClient();
	return createRouter({
		routeTree,
		context: { queryClient },
		scrollRestoration: true,
		defaultPreloadStaleTime: 0
	});
};
//#endregion
export { DropdownMenuCheckboxItem as a, DropdownMenuLabel as c, Badge as d, Skeleton as f, getRouter, Button as h, DropdownMenu as i, DropdownMenuSeparator as l, Input as m, Route as n, DropdownMenuContent as o, Separator as p, Route$1 as r, DropdownMenuItem as s, router_exports as t, DropdownMenuTrigger as u };
