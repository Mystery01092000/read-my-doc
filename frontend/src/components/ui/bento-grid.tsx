import { cn } from "@/lib/utils";
import React from "react";

export interface BentoItem {
    title: string;
    description: string;
    icon: React.ReactNode;
    status?: string;
    tags?: string[];
    meta?: string;
    cta?: string;
    onClick?: () => void;
    colSpan?: number;
    hasPersistentHover?: boolean;
    className?: string;
}

interface BentoGridProps {
    items: BentoItem[];
    className?: string;
}

export function BentoGrid({ items, className }: BentoGridProps) {
    return (
        <div className={cn("grid grid-cols-1 md:grid-cols-3 gap-3", className)}>
            {items.map((item, index) => (
                <div
                    key={index}
                    onClick={item.onClick}
                    className={cn(
                        "group relative p-4 rounded-xl overflow-hidden transition-all duration-300",
                        "border border-white/5 bg-surface-container-low text-on-surface",
                        "hover:shadow-[0_2px_12px_rgba(255,255,255,0.03)]",
                        "hover:-translate-y-0.5 will-change-transform",
                        item.onClick && "cursor-pointer",
                        item.colSpan === 2 ? "md:col-span-2" : "col-span-1",
                        item.hasPersistentHover && "shadow-[0_2px_12px_rgba(255,255,255,0.03)] -translate-y-0.5",
                        item.className
                    )}
                >
                    {/* Background Pattern */}
                    <div
                        className={cn(
                            "absolute inset-0 transition-opacity duration-300",
                            item.hasPersistentHover ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                        )}
                    >
                        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[length:4px_4px]" />
                    </div>

                    <div className="relative flex flex-col space-y-3">
                        <div className="flex items-center justify-between">
                            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-white/10 group-hover:bg-primary/20 transition-all duration-300">
                                {item.icon}
                            </div>
                            {item.status && (
                                <span
                                    className="text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded-lg bg-white/5 text-on-surface-variant transition-colors duration-300 group-hover:bg-white/10"
                                >
                                    {item.status}
                                </span>
                            )}
                        </div>

                        <div className="space-y-1">
                            <h3 className="font-bold text-[#e2e2e2] tracking-tight text-sm flex items-center gap-2">
                                {item.title}
                                {item.meta && (
                                    <span className="text-[10px] text-on-surface-variant font-normal uppercase tracking-widest opacity-60">
                                        {item.meta}
                                    </span>
                                )}
                            </h3>
                            <p className="text-xs text-on-surface-variant leading-relaxed font-medium">
                                {item.description}
                            </p>
                        </div>

                        <div className="flex items-center justify-between mt-2">
                            <div className="flex items-center space-x-2 text-[9px] font-bold uppercase tracking-widest">
                                {item.tags?.map((tag, i) => (
                                    <span
                                        key={i}
                                        className="px-2 py-1 rounded-md bg-white/5 backdrop-blur-sm transition-all duration-200 hover:bg-white/10 text-on-surface-variant"
                                    >
                                        #{tag}
                                    </span>
                                ))}
                            </div>
                            {item.cta && (
                                <span className={cn(
                                    "text-[10px] font-bold text-primary opacity-0 group-hover:opacity-100 transition-opacity uppercase tracking-widest flex items-center gap-1",
                                    item.cta.includes("Purge") && "text-red-400 group-hover:text-red-500"
                                )}>
                                    {item.cta} →
                                </span>
                            )}
                        </div>
                    </div>

                    {/* Gradient Border Overlay */}
                    <div
                        className={cn(
                            "absolute inset-0 -z-10 rounded-xl p-px bg-gradient-to-br from-transparent via-white/10 to-transparent transition-opacity duration-300",
                            item.hasPersistentHover ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                        )}
                    />
                </div>
            ))}
        </div>
    );
}
