import React, { useState, useRef, useEffect } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '../../lib/utils'

interface SelectProps {
  value: string
  onValueChange: (value: string) => void
  children: React.ReactNode
  disabled?: boolean
  placeholder?: string
}

interface SelectTriggerProps {
  children: React.ReactNode
  className?: string
}

interface SelectContentProps {
  children: React.ReactNode
  className?: string
}

interface SelectItemProps {
  value: string
  children: React.ReactNode
  className?: string
}

interface SelectValueProps {
  placeholder?: string
}

const SelectContext = React.createContext<{
  value: string
  onValueChange: (value: string) => void
  isOpen: boolean
  setIsOpen: (open: boolean) => void
  disabled?: boolean
} | null>(null)

export function Select({ value, onValueChange, children, disabled }: SelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const selectRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <SelectContext.Provider value={{ value, onValueChange, isOpen, setIsOpen, disabled }}>
      <div ref={selectRef} className="relative">
        {children}
      </div>
    </SelectContext.Provider>
  )
}

export function SelectTrigger({ children, className }: SelectTriggerProps) {
  const context = React.useContext(SelectContext)
  if (!context) throw new Error('SelectTrigger must be used within Select')

  const { isOpen, setIsOpen, disabled } = context

  return (
    <button
      type="button"
      onClick={() => !disabled && setIsOpen(!isOpen)}
      disabled={disabled}
      className={cn(
        'flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
    >
      {children}
      <ChevronDown className={cn('h-4 w-4 opacity-50 transition-transform', isOpen && 'rotate-180')} />
    </button>
  )
}

export function SelectContent({ children, className }: SelectContentProps) {
  const context = React.useContext(SelectContext)
  if (!context) throw new Error('SelectContent must be used within Select')

  const { isOpen } = context

  if (!isOpen) return null

  return (
    <div
      className={cn(
        'absolute top-full z-50 mt-1 w-full rounded-md border bg-popover p-1 text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95',
        className
      )}
    >
      {children}
    </div>
  )
}

export function SelectItem({ value, children, className }: SelectItemProps) {
  const context = React.useContext(SelectContext)
  if (!context) throw new Error('SelectItem must be used within Select')

  const { value: selectedValue, onValueChange, setIsOpen } = context

  const handleClick = () => {
    onValueChange(value)
    setIsOpen(false)
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={cn(
        'relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
        selectedValue === value && 'bg-accent text-accent-foreground',
        className
      )}
    >
      {children}
    </button>
  )
}

export function SelectValue({ placeholder }: SelectValueProps) {
  const context = React.useContext(SelectContext)
  if (!context) throw new Error('SelectValue must be used within Select')

  const { value } = context

  // 在实际应用中，这里应该根据选中的值显示对应的文本
  // 为了简化，这里直接显示值
  return (
    <span className={cn(!value && 'text-muted-foreground')}>
      {value || placeholder}
    </span>
  )
}