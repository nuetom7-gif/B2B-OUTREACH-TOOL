import { x as cn } from "./hooks-DJqooqkf.js";
import * as React from "react";
import { jsx, jsxs } from "react/jsx-runtime";
//#region src/components/ui/card.tsx
var Card = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("div", {
	ref,
	className: cn("rounded-xl border bg-card text-card-foreground shadow", className),
	...props
}));
Card.displayName = "Card";
var CardHeader = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("div", {
	ref,
	className: cn("flex flex-col space-y-1.5 p-6", className),
	...props
}));
CardHeader.displayName = "CardHeader";
var CardTitle = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("div", {
	ref,
	className: cn("font-semibold leading-none tracking-tight", className),
	...props
}));
CardTitle.displayName = "CardTitle";
var CardDescription = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("div", {
	ref,
	className: cn("text-sm text-muted-foreground", className),
	...props
}));
CardDescription.displayName = "CardDescription";
var CardContent = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("div", {
	ref,
	className: cn("p-6 pt-0", className),
	...props
}));
CardContent.displayName = "CardContent";
var CardFooter = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("div", {
	ref,
	className: cn("flex items-center p-6 pt-0", className),
	...props
}));
CardFooter.displayName = "CardFooter";
//#endregion
//#region src/components/shared/page-header.tsx
function PageHeader({ title, description, actions }) {
	return /* @__PURE__ */ jsxs("header", {
		className: "grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3 sm:flex sm:flex-wrap sm:items-center sm:justify-between",
		children: [/* @__PURE__ */ jsxs("div", {
			className: "min-w-0",
			children: [/* @__PURE__ */ jsx("h1", {
				className: "truncate text-xl font-semibold sm:text-2xl",
				children: title
			}), description ? /* @__PURE__ */ jsx("p", {
				className: "mt-1 text-sm text-muted-foreground",
				children: description
			}) : null]
		}), actions ? /* @__PURE__ */ jsx("div", {
			className: "flex shrink-0 flex-wrap gap-2",
			children: actions
		}) : null]
	});
}
function SectionCardTitle({ title, hint }) {
	return /* @__PURE__ */ jsxs("div", {
		className: "min-w-0",
		children: [/* @__PURE__ */ jsx("h2", {
			className: "truncate text-sm font-semibold",
			children: title
		}), hint ? /* @__PURE__ */ jsx("p", {
			className: "text-xs text-muted-foreground",
			children: hint
		}) : null]
	});
}
function StateCard({ title, description, action }) {
	return /* @__PURE__ */ jsx(Card, { children: /* @__PURE__ */ jsxs(CardContent, {
		className: "flex min-h-40 flex-col items-start justify-center gap-3 py-8 text-sm",
		children: [/* @__PURE__ */ jsxs("div", {
			className: "space-y-1",
			children: [/* @__PURE__ */ jsx("p", {
				className: "font-medium",
				children: title
			}), /* @__PURE__ */ jsx("p", {
				className: "text-muted-foreground",
				children: description
			})]
		}), action ? /* @__PURE__ */ jsx("div", { children: action }) : null]
	}) });
}
//#endregion
export { CardContent as a, Card as i, SectionCardTitle as n, CardHeader as o, StateCard as r, PageHeader as t };
