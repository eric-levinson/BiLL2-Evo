'use client'
import * as React from 'react'
import * as RadixDropdown from '@radix-ui/react-dropdown-menu'
import { cn } from '@/lib/utils'

const DropdownMenu = RadixDropdown.Root
const DropdownMenuTrigger = RadixDropdown.Trigger
const DropdownMenuPortal = RadixDropdown.Portal
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const DropdownMenuContent = ({ className, ...props }: any) => (
  // use an explicit opaque popover background and high z-index so the menu
  // doesn't appear behind app content
  <RadixDropdown.Content
    className={cn(
      'z-50 min-w-[220px] rounded-md border bg-white p-1 shadow-md dark:bg-gray-800',
      className
    )}
    {...props}
  />
)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const DropdownMenuItem = ({ className, ...props }: any) => (
  // make items block-level and full width so anchors stack vertically when
  // `asChild` is used (prevents inline anchors on the same row)
  <RadixDropdown.Item
    className={cn(
      'block w-full px-3 py-2 text-sm leading-none text-black hover:bg-accent/50 dark:text-white',
      className
    )}
    {...props}
  />
)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const DropdownMenuLabel = ({ className, ...props }: any) => (
  <div
    className={cn(
      'px-3 py-1 text-xs font-medium text-black/60 dark:text-white/80',
      className
    )}
    {...props}
  />
)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const DropdownMenuSeparator = (props: any) => (
  <RadixDropdown.Separator className="mx-1 my-2 h-px bg-muted" {...props} />
)

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuPortal,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator
}

export default DropdownMenu
