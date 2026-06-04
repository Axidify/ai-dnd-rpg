import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'

export default function Modal({
  open,
  onClose,
  title,
  eyebrow,
  maxWidth = 'max-w-xl',
  children,
  titleId = 'modal-title',
}) {
  useEffect(() => {
    if (!open) return
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18 }}
        >
          <div
            className="absolute inset-0 bg-black/70 backdrop-blur-[3px]"
            onClick={onClose}
            aria-hidden
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            initial={{ opacity: 0, y: 24, scale: 0.99 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.99 }}
            transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
            className={`relative w-full ${maxWidth} max-h-[90vh] sm:max-h-[85vh] flex flex-col panel rounded-t-2xl sm:rounded-2xl overflow-hidden`}
          >
            <header className="shrink-0 flex items-center justify-between gap-4 px-5 sm:px-7 pt-5 pb-4 border-b border-[var(--line)]">
              <div className="min-w-0">
                {eyebrow && <p className="caps-muted mb-1">{eyebrow}</p>}
                <h2 id={titleId} className="display text-2xl sm:text-[1.7rem] truncate">
                  {title}
                </h2>
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label="Close"
                className="focus-ring shrink-0 w-9 h-9 rounded-full grid place-items-center text-[var(--ink-3)] hover:text-[var(--gold)] hover:bg-[var(--gold-soft)] transition"
              >
                <X size={18} />
              </button>
            </header>
            <div className="overflow-y-auto px-5 sm:px-7 py-5 sm:py-6">{children}</div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
