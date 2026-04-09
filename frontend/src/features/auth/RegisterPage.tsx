import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { UserPlus, ArrowRight } from "lucide-react";

export function RegisterPage() {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const { register, isLoading, error } = useAuth();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    if (!name.trim()) {
      setLocalError("Name is required");
      return;
    }
    if (password !== confirm) {
      setLocalError("Passwords do not match");
      return;
    }
    if (password.length < 8) {
      setLocalError("Password must be at least 8 characters");
      return;
    }
    await register(name.trim(), phone.trim(), email, password);
  };

  const displayError = localError ?? error;

  const inputClass =
    "w-full bg-surface-container-lowest border border-outline-variant/10 rounded-lg px-4 py-2 text-on-surface focus:outline-none focus:ring-1 focus:ring-primary/40 transition-all placeholder:text-outline/40";

  return (
    <main className="flex-grow flex items-center justify-center p-6 md:p-12 relative overflow-hidden min-h-screen">
      {/* Abstract Background Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/10 blur-[120px] rounded-full pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[30%] h-[30%] bg-secondary/10 blur-[100px] rounded-full pointer-events-none"></div>

      {/* Main Bento Container */}
      <div className="glass-panel w-full max-w-4xl rounded-xl p-8 md:p-12 grid grid-cols-1 md:grid-cols-12 gap-6 relative z-10">
        {/* Branding & Title Section */}
        <div className="md:col-span-12 flex flex-col items-center mb-4">
          <h1 className="font-headline font-bold text-4xl md:text-5xl tracking-tighter text-primary mb-2">ReadMyDoc</h1>
          <p className="font-label text-on-surface-variant text-sm tracking-wide uppercase">Create your account to get started.</p>
        </div>

        {/* Left Column: Illustration/Decorative */}
        <div className="hidden md:flex md:col-span-5 bento-inner flex-col justify-between p-8 overflow-hidden relative">
          <div className="relative z-10">
            <UserPlus className="text-primary w-10 h-10 mb-4" />
            <h2 className="font-headline text-2xl font-bold leading-tight mb-4 text-on-surface">Join ReadMyDoc.</h2>
            <p className="text-on-surface-variant text-sm leading-relaxed">Upload documents and start chatting with your personal knowledge base instantly.</p>
          </div>
        </div>

        {/* Right Column: Register Form */}
        <div className="md:col-span-7 flex flex-col gap-6">
          <div className="bento-inner p-8 h-full">
            {displayError && (
              <div className="mb-6 rounded-md bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
                {displayError}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label className="font-label text-xs font-bold text-on-surface-variant uppercase tracking-widest ml-1">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className={inputClass}
                  placeholder="Your full name"
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="font-label text-xs font-bold text-on-surface-variant uppercase tracking-widest ml-1">Phone (optional)</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className={inputClass}
                  placeholder="+1 234 567 8900"
                />
              </div>

              <div className="space-y-2">
                <label className="font-label text-xs font-bold text-on-surface-variant uppercase tracking-widest ml-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={inputClass}
                  placeholder="you@example.com"
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="font-label text-xs font-bold text-on-surface-variant uppercase tracking-widest ml-1">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={inputClass}
                  placeholder="Min. 8 characters"
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="font-label text-xs font-bold text-on-surface-variant uppercase tracking-widest ml-1">Confirm Password</label>
                <input
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  className={inputClass}
                  placeholder="••••••••"
                  required
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="metallic-gradient w-full py-4 rounded-xl font-headline font-bold text-[#002e6a] tracking-tight hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? "Creating account..." : "Create Account"}
                  {!isLoading && <ArrowRight className="w-5 h-5" />}
                </button>
              </div>
            </form>
          </div>

          {/* Footer Links */}
          <div className="grid grid-cols-2 gap-4">
            <Link to="/login" className="bento-inner bg-surface-container-high/40 rounded-xl p-4 flex flex-col justify-center items-center group cursor-pointer hover:bg-surface-container-high transition-colors">
              <span className="font-label text-[10px] text-on-surface-variant uppercase tracking-widest mb-1">Have an account?</span>
              <span className="text-primary font-bold text-sm group-hover:text-white transition-colors">Sign In</span>
            </Link>
            <div className="bento-inner bg-surface-container-high/40 rounded-xl p-4 flex flex-col justify-center items-center">
              <span className="font-label text-[10px] text-on-surface-variant uppercase tracking-widest mb-1">Version</span>
              <span className="text-on-surface font-bold text-sm">v2.4.1</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
