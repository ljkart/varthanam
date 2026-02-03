import { forwardRef, type ButtonHTMLAttributes } from "react";
import styles from "./Button.module.css";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline";
  fullWidth?: boolean;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      fullWidth = false,
      isLoading = false,
      leftIcon,
      children,
      className,
      disabled,
      ...props
    },
    ref,
  ) => {
    return (
      <button
        ref={ref}
        className={`${styles.button} ${styles[variant]} ${fullWidth ? styles.fullWidth : ""} ${className || ""}`}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <span className={styles.spinner} />
        ) : (
          <>
            {leftIcon && <span className={styles.icon}>{leftIcon}</span>}
            {children}
          </>
        )}
      </button>
    );
  },
);

Button.displayName = "Button";
