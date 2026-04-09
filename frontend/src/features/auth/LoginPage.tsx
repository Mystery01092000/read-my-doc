import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Unlock, ArrowRight } from "lucide-react";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { login, isLoading, error } = useAuth();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await login(email, password);
  };

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
          <p className="font-label text-on-surface-variant text-sm tracking-wide uppercase">Secure access to your document corpus. Meta: v2.4.1.</p>
        </div>

        {/* Left Column: Illustration/Decorative */}
        <div className="hidden md:flex md:col-span-5 bento-inner flex-col justify-between p-8 overflow-hidden relative">
          <div className="relative z-10">
            <Unlock className="text-primary w-10 h-10 mb-4" />
            <h2 className="font-headline text-2xl font-bold leading-tight mb-4 text-on-surface">Encrypted Document Intelligence.</h2>
            <p className="text-on-surface-variant text-sm leading-relaxed">Experience a vault-grade interface designed for architectural clarity and high-fidelity interaction.</p>
          </div>
          <div className="mt-8 relative h-32">
            <img
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuAtzkZAJr_3tabco4eCshDkB1QAc8sq1y94sBMHhKBb40ZmSSlieeEbRUFhF3Vv_kjyaHE9xvG15sV37puucGcPix0iItmRxE4_5eEgy50krcKA7veck1o6o5CC3FgzyN9bFoM4TmsgQ0B69P1Km1kt2_tBiMIzEtssIdsMpk5b8brGcx6EZhrIefHNiQQjmRBMcq4zyRpUdoHPk_cuildrzETZdZ2ap4g-BlgOxkEu5Xxc8347UfBXsUTDEaCfWwiV5X9Htii6ayU"
              alt="Abstract digital vault"
              className="absolute inset-0 w-full h-full object-cover rounded-lg opacity-40 mix-blend-screen"
            />
          </div>
        </div>

        {/* Right Column: Login Form */}
        <div className="md:col-span-7 flex flex-col gap-6">
          <div className="bento-inner p-8 h-full">
            {error && (
              <div className="mb-6 rounded-md bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <label className="font-label text-xs font-bold text-on-surface-variant uppercase tracking-widest ml-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-surface-container-lowest border border-outline-variant/10 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-1 focus:ring-primary/40 transition-all placeholder:text-outline/40"
                  placeholder="name@architecture.com"
                  required
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center px-1">
                  <label className="font-label text-xs font-bold text-on-surface-variant uppercase tracking-widest">Password</label>
                  <Link to="#" className="text-[10px] text-primary hover:text-white transition-colors font-bold uppercase tracking-tighter">Forgot Password?</Link>
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-surface-container-lowest border border-outline-variant/10 rounded-lg px-4 py-3 text-on-surface focus:outline-none focus:ring-1 focus:ring-primary/40 transition-all placeholder:text-outline/40"
                  placeholder="••••••••"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="metallic-gradient w-full py-4 rounded-xl font-headline font-bold text-[#002e6a] tracking-tight hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? "Authenticating..." : "Authenticate System"}
                {!isLoading && <ArrowRight className="w-5 h-5" />}
              </button>
            </form>
          </div>

          {/* Footer Links integrated into grid */}
          <div className="grid grid-cols-2 gap-4">
            <Link to="/register" className="bento-inner bg-surface-container-high/40 rounded-xl p-4 flex flex-col justify-center items-center group cursor-pointer hover:bg-surface-container-high transition-colors">
              <span className="font-label text-[10px] text-on-surface-variant uppercase tracking-widest mb-1">New Researcher?</span>
              <span className="text-primary font-bold text-sm group-hover:text-white transition-colors">Request Access</span>
            </Link>
            <div className="bento-inner bg-surface-container-high/40 rounded-xl p-4 flex flex-col justify-center items-center">
              <span className="font-label text-[10px] text-on-surface-variant uppercase tracking-widest mb-1">Architecture</span>
              <span className="text-on-surface font-bold text-sm">v2.4.1 Node</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
