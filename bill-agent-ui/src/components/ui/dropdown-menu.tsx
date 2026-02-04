"use client"
import * as React from "react"
import * as RadixDropdown from "@radix-ui/react-dropdown-menu"
import { cn } from '@/lib/utils'

const DropdownMenu = RadixDropdown.Root
const DropdownMenuTrigger = RadixDropdown.Trigger
const DropdownMenuPortal = RadixDropdown.Portal
const DropdownMenuContent = ({ className, ...props }: any) => (
    // use an explicit opaque popover background and high z-index so the menu
    // doesn't appear behind app content
    <RadixDropdown.Content
        className={cn(
            "min-w-[220px] rounded-md border bg-white dark:bg-gray-800 p-1 shadow-md z-50",
            className
        )}
        {...props}
    />
)
const DropdownMenuItem = ({ className, ...props }: any) => (
    // make items block-level and full width so anchors stack vertically when
    // `asChild` is used (prevents inline anchors on the same row)
    <RadixDropdown.Item
        className={cn("block w-full px-3 py-2 text-sm leading-none text-black dark:text-white hover:bg-accent/50", className)}
        {...props}
    />
)
const DropdownMenuLabel = ({ className, ...props }: any) => (
    <div className={cn("px-3 py-1 text-xs font-medium text-black/60 dark:text-white/80", className)} {...props} />
)
const DropdownMenuSeparator = (props: any) => <RadixDropdown.Separator className="mx-1 my-2 h-px bg-muted" {...props} />

export {
    DropdownMenu,
    DropdownMenuTrigger,
    DropdownMenuPortal,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
}

export default DropdownMenu
