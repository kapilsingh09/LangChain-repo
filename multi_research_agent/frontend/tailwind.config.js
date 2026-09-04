/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0F19',
        surface: '#151A27',
        'surface-hover': '#1E2536',
        border: '#2A3245',
        primary: '#4F46E5', // Indigo
        secondary: '#94A3B8',
        'text-main': '#F8FAFC',
        'text-muted': '#94A3B8',
        'status-success': '#10B981',
        'status-error': '#EF4444',
        'status-pending': '#F59E0B',
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
