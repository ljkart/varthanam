import { useAuth } from "../lib/auth";
import { Button, Logo } from "../components/ui";
import styles from "./Home.module.css";

export function HomePage() {
  const { user, logout, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className={styles.page}>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Logo />
      {user ? (
        <div className={styles.content}>
          <h1 className={styles.title}>
            Welcome, {user.full_name || user.email}!
          </h1>
          <p className={styles.subtitle}>You are logged in.</p>
          <Button onClick={logout} variant="secondary">
            Sign Out
          </Button>
        </div>
      ) : (
        <div className={styles.content}>
          <h1 className={styles.title}>Welcome to Varthanam</h1>
          <p className={styles.subtitle}>Your personalized news aggregator</p>
          <div className={styles.actions}>
            <Button onClick={() => (window.location.href = "/login")}>
              Sign In
            </Button>
            <Button
              onClick={() => (window.location.href = "/register")}
              variant="secondary"
            >
              Sign Up
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
