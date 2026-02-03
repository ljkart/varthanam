## Summary

Implements the Login and Register screens for the Varthanam frontend, following the Pencil.ai design specifications exactly.

### What's included:

- **React SPA Setup**: Vite + React 18 + TypeScript + React Router
- **Design System**: CSS tokens derived from Pencil.ai design (dark theme, lime green accent)
- **Reusable UI Components**:
  - `Input` - Text input with label, password toggle, and error state
  - `Button` - Primary, secondary, and outline variants with loading state
  - `Logo` - Varthanam brand logo component
- **API Integration**:
  - Typed API client (`src/lib/api.ts`) with login/register/getCurrentUser methods
  - Auth helpers (`src/lib/auth.ts`) with token management and AuthContext
  - AuthProvider component for app-wide auth state
- **Auth Pages**:
  - Login page with email/password form, forgot password link, Google sign-in placeholder
  - Register page with full name/email/password form, terms acceptance
  - Error handling and loading states

### Design Adherence

The implementation follows the Pencil.ai design exactly:

- Dark background (#000000) with card background (#0A0A0A)
- Lime green primary accent (#BFFF00)
- Inter font for headings, JetBrains Mono for body text
- 48px input height, consistent spacing (8px, 16px, 20px, 28px, 32px, 40px)
- Password visibility toggle with eye icons

## Test plan

- [ ] Run `npm run lint` - passes
- [ ] Run `npm run build` - builds successfully
- [ ] Manual testing:
  - [ ] Visit `/login` - displays login form matching Pencil design
  - [ ] Visit `/register` - displays register form matching Pencil design
  - [ ] Submit login with valid credentials - authenticates and redirects
  - [ ] Submit login with invalid credentials - displays error message
  - [ ] Submit register - creates account and redirects to login
  - [ ] Password field shows/hides on toggle click
  - [ ] Links between login/register work correctly

## Screenshots

| Login Screen                   | Register Screen                      |
| ------------------------------ | ------------------------------------ |
| ![Login](login-screenshot.png) | ![Register](register-screenshot.png) |

_(Screenshots to be added after visual verification)_

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
