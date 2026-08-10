"use client";

import {ReactNode, useEffect, useId} from "react";

type FormDialogProps = {
  open: boolean;
  title: string;
  description?: string;
  children: ReactNode;
  onClose: () => void;
  width?: "sm" | "md" | "lg";
  closeDisabled?: boolean;
};

const widths = {
  sm: "max-w-md",
  md: "max-w-2xl",
  lg: "max-w-4xl",
};

/** پنجرهٔ یکپارچه برای ثبت و ویرایش داده در کافینو. */
export default function FormDialog({
  open,
  title,
  description,
  children,
  onClose,
  width = "md",
  closeDisabled = false,
}: FormDialogProps) {
  const titleId = useId();
  const descriptionId = useId();

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !closeDisabled) onClose();
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [closeDisabled, onClose, open]);

  if (!open) return null;

  return (
    <div className="dialog-layer" role="presentation">
      <button
        aria-label="بستن پنجره"
        className="dialog-backdrop"
        disabled={closeDisabled}
        onClick={onClose}
      />
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descriptionId : undefined}
        className={`dialog-panel ${widths[width]}`}
      >
        <header className="dialog-header">
          <div>
            <h2 id={titleId} className="text-xl font-black">{title}</h2>
            {description && <p id={descriptionId} className="mt-1 text-sm text-[#8d8178]">{description}</p>}
          </div>
          <button type="button" className="dialog-close" onClick={onClose} disabled={closeDisabled} aria-label="بستن">
            ×
          </button>
        </header>
        <div className="dialog-content">{children}</div>
      </section>
    </div>
  );
}
