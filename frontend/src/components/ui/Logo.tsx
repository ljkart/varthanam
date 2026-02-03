import styles from "./Logo.module.css";

export interface LogoProps {
  size?: "sm" | "md" | "lg";
}

export function Logo({ size = "md" }: LogoProps) {
  const dimensions = {
    sm: 24,
    md: 32,
    lg: 48,
  };

  const fontSize = {
    sm: 14,
    md: 20,
    lg: 28,
  };

  return (
    <div className={styles.container}>
      <div
        className={styles.mark}
        style={{
          width: dimensions[size],
          height: dimensions[size],
        }}
      />
      <span className={styles.text} style={{ fontSize: fontSize[size] }}>
        VARTHANAM
      </span>
    </div>
  );
}
