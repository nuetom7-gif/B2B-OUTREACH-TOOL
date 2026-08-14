import { x as cn } from "./hooks-xnZ2zKrZ.js";
import { a as DropdownMenuCheckboxItem, c as DropdownMenuLabel, f as Skeleton, h as Button, i as DropdownMenu, m as Input, o as DropdownMenuContent, u as DropdownMenuTrigger } from "./router-CjNjiVPZ.js";
import * as React from "react";
import { useState } from "react";
import { jsx, jsxs } from "react/jsx-runtime";
import { ArrowUpDown, Check, ChevronLeft, ChevronRight, Search, SlidersHorizontal } from "lucide-react";
import { flexRender, getCoreRowModel, getFilteredRowModel, getPaginationRowModel, getSortedRowModel, useReactTable } from "@tanstack/react-table";
import * as CheckboxPrimitive from "@radix-ui/react-checkbox";
//#region src/components/ui/table.tsx
var Table = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("div", {
	className: "relative w-full overflow-auto",
	children: /* @__PURE__ */ jsx("table", {
		ref,
		className: cn("w-full caption-bottom text-sm", className),
		...props
	})
}));
Table.displayName = "Table";
var TableHeader = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("thead", {
	ref,
	className: cn("[&_tr]:border-b", className),
	...props
}));
TableHeader.displayName = "TableHeader";
var TableBody = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("tbody", {
	ref,
	className: cn("[&_tr:last-child]:border-0", className),
	...props
}));
TableBody.displayName = "TableBody";
var TableFooter = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("tfoot", {
	ref,
	className: cn("border-t bg-muted/50 font-medium [&>tr]:last:border-b-0", className),
	...props
}));
TableFooter.displayName = "TableFooter";
var TableRow = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("tr", {
	ref,
	className: cn("border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted", className),
	...props
}));
TableRow.displayName = "TableRow";
var TableHead = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("th", {
	ref,
	className: cn("h-10 px-2 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px]", className),
	...props
}));
TableHead.displayName = "TableHead";
var TableCell = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("td", {
	ref,
	className: cn("p-2 align-middle [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px]", className),
	...props
}));
TableCell.displayName = "TableCell";
var TableCaption = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx("caption", {
	ref,
	className: cn("mt-4 text-sm text-muted-foreground", className),
	...props
}));
TableCaption.displayName = "TableCaption";
//#endregion
//#region src/components/shared/data-table.tsx
function DataTable({ columns, data, searchPlaceholder = "Search…", toolbar, bulkActions, onRowClick, loading, pageSize = 10, emptyMessage = "No records match the current filters." }) {
	const [sorting, setSorting] = useState([]);
	const [globalFilter, setGlobalFilter] = useState("");
	const [rowSelection, setRowSelection] = useState({});
	const [columnVisibility, setColumnVisibility] = useState({});
	const table = useReactTable({
		data,
		columns,
		state: {
			sorting,
			globalFilter,
			rowSelection,
			columnVisibility
		},
		onSortingChange: setSorting,
		onGlobalFilterChange: setGlobalFilter,
		onRowSelectionChange: setRowSelection,
		onColumnVisibilityChange: setColumnVisibility,
		getCoreRowModel: getCoreRowModel(),
		getSortedRowModel: getSortedRowModel(),
		getFilteredRowModel: getFilteredRowModel(),
		getPaginationRowModel: getPaginationRowModel(),
		initialState: { pagination: { pageSize } },
		enableRowSelection: true
	});
	const selected = table.getSelectedRowModel().rows.map((r) => r.original);
	return /* @__PURE__ */ jsxs("div", {
		className: "space-y-3",
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "grid grid-cols-[minmax(0,1fr)_auto] items-center gap-2 sm:flex sm:flex-wrap",
				children: [
					/* @__PURE__ */ jsxs("div", {
						className: "relative min-w-0 sm:w-72",
						children: [/* @__PURE__ */ jsx(Search, { className: "absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" }), /* @__PURE__ */ jsx(Input, {
							value: globalFilter,
							onChange: (e) => setGlobalFilter(e.target.value),
							placeholder: searchPlaceholder,
							className: "h-9 pl-8"
						})]
					}),
					toolbar,
					/* @__PURE__ */ jsxs(DropdownMenu, { children: [/* @__PURE__ */ jsx(DropdownMenuTrigger, {
						asChild: true,
						children: /* @__PURE__ */ jsxs(Button, {
							variant: "outline",
							size: "sm",
							className: "h-9 shrink-0 gap-1.5 sm:ml-auto",
							children: [/* @__PURE__ */ jsx(SlidersHorizontal, { className: "size-3.5" }), /* @__PURE__ */ jsx("span", {
								className: "hidden sm:inline",
								children: "Columns"
							})]
						})
					}), /* @__PURE__ */ jsxs(DropdownMenuContent, {
						align: "end",
						className: "w-48",
						children: [/* @__PURE__ */ jsx(DropdownMenuLabel, { children: "Visible columns" }), table.getAllLeafColumns().filter((c) => c.getCanHide()).map((column) => /* @__PURE__ */ jsx(DropdownMenuCheckboxItem, {
							checked: column.getIsVisible(),
							onCheckedChange: (v) => column.toggleVisibility(!!v),
							className: "capitalize",
							children: column.id.replace(/_/g, " ")
						}, column.id))]
					})] })
				]
			}),
			selected.length > 0 && bulkActions ? /* @__PURE__ */ jsxs("div", {
				className: "flex flex-wrap items-center gap-2 rounded-md border bg-accent/40 px-3 py-2",
				children: [/* @__PURE__ */ jsxs("span", {
					className: "text-sm font-medium",
					children: [selected.length, " selected"]
				}), /* @__PURE__ */ jsx("div", {
					className: "ml-auto flex flex-wrap gap-2",
					children: bulkActions(selected, () => setRowSelection({}))
				})]
			}) : null,
			/* @__PURE__ */ jsx("div", {
				className: "overflow-hidden rounded-lg border bg-card shadow-[var(--shadow-card)]",
				children: /* @__PURE__ */ jsx("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ jsxs(Table, { children: [/* @__PURE__ */ jsx(TableHeader, {
						className: "bg-muted/40",
						children: table.getHeaderGroups().map((hg) => /* @__PURE__ */ jsx(TableRow, {
							className: "hover:bg-transparent",
							children: hg.headers.map((header) => /* @__PURE__ */ jsx(TableHead, {
								className: "h-10 whitespace-nowrap",
								children: header.isPlaceholder ? null : header.column.getCanSort() ? /* @__PURE__ */ jsxs("button", {
									className: "flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground hover:text-foreground",
									onClick: header.column.getToggleSortingHandler(),
									children: [flexRender(header.column.columnDef.header, header.getContext()), /* @__PURE__ */ jsx(ArrowUpDown, { className: "size-3 opacity-60" })]
								}) : flexRender(header.column.columnDef.header, header.getContext())
							}, header.id))
						}, hg.id))
					}), /* @__PURE__ */ jsx(TableBody, { children: loading ? Array.from({ length: 6 }).map((_, i) => /* @__PURE__ */ jsx(TableRow, { children: table.getVisibleLeafColumns().map((c) => /* @__PURE__ */ jsx(TableCell, { children: /* @__PURE__ */ jsx(Skeleton, { className: "h-4 w-full max-w-[140px]" }) }, c.id)) }, i)) : table.getRowModel().rows.length === 0 ? /* @__PURE__ */ jsx(TableRow, { children: /* @__PURE__ */ jsx(TableCell, {
						colSpan: table.getVisibleLeafColumns().length,
						className: "h-28 text-center text-sm text-muted-foreground",
						children: emptyMessage
					}) }) : table.getRowModel().rows.map((row) => /* @__PURE__ */ jsx(TableRow, {
						"data-state": row.getIsSelected() ? "selected" : void 0,
						className: cn(onRowClick && "cursor-pointer"),
						onClick: (e) => {
							if (e.target.closest("[data-no-row-click]")) return;
							onRowClick?.(row.original);
						},
						children: row.getVisibleCells().map((cell) => /* @__PURE__ */ jsx(TableCell, {
							className: "py-2.5",
							children: flexRender(cell.column.columnDef.cell, cell.getContext())
						}, cell.id))
					}, row.id)) })] })
				})
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "flex flex-wrap items-center justify-between gap-2 text-sm text-muted-foreground",
				children: [/* @__PURE__ */ jsxs("span", { children: [
					table.getFilteredRowModel().rows.length,
					" record",
					table.getFilteredRowModel().rows.length === 1 ? "" : "s"
				] }), /* @__PURE__ */ jsxs("div", {
					className: "flex items-center gap-2",
					children: [
						/* @__PURE__ */ jsxs("span", {
							className: "text-numeric",
							children: [
								"Page ",
								table.getState().pagination.pageIndex + 1,
								" of ",
								table.getPageCount() || 1
							]
						}),
						/* @__PURE__ */ jsx(Button, {
							variant: "outline",
							size: "icon",
							className: "size-8",
							onClick: () => table.previousPage(),
							disabled: !table.getCanPreviousPage(),
							children: /* @__PURE__ */ jsx(ChevronLeft, { className: "size-4" })
						}),
						/* @__PURE__ */ jsx(Button, {
							variant: "outline",
							size: "icon",
							className: "size-8",
							onClick: () => table.nextPage(),
							disabled: !table.getCanNextPage(),
							children: /* @__PURE__ */ jsx(ChevronRight, { className: "size-4" })
						})
					]
				})]
			})
		]
	});
}
//#endregion
//#region src/components/ui/checkbox.tsx
var Checkbox = React.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsx(CheckboxPrimitive.Root, {
	ref,
	className: cn("grid place-content-center peer h-4 w-4 shrink-0 rounded-sm border border-primary shadow cursor-pointer focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground", className),
	...props,
	children: /* @__PURE__ */ jsx(CheckboxPrimitive.Indicator, {
		className: cn("grid place-content-center text-current"),
		children: /* @__PURE__ */ jsx(Check, { className: "h-4 w-4" })
	})
}));
Checkbox.displayName = CheckboxPrimitive.Root.displayName;
//#endregion
export { DataTable as n, Checkbox as t };
