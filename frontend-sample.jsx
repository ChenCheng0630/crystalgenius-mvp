import React, { useState } from "react";
import { Trophy, Send, Star, ShoppingCart, Tag, MessageCircle } from "lucide-react";

// -------------------- Types --------------------
type Product = {
  id: number;
  title: string;
  price: number;
  compareAt?: number; // 原价，用于计算折扣
  sold?: string;
  rating?: number;
  reviews?: number;
  image: string;
};

type Guide = {
  name: string;
  avatar: string;
  introShort: string;
  domains: string[];
  styles: string[];
  monthlySales: string;
  gmv: string;
  positiveRate: string;
};

// -------------------- Utils + Tiny Tests --------------------
export function discountPct(price: number, compareAt?: number): number {
  if (!compareAt || compareAt <= 0 || compareAt <= price) return 0;
  return Math.round((1 - price / compareAt) * 100);
}

// 轻量断言，避免回归（只在浏览器执行）
if (typeof window !== "undefined") {
  console.assert(discountPct(80, 100) === 20, "discount 20% expected");
  console.assert(discountPct(100, 100) === 0, "no discount when equal");
  console.assert(discountPct(120, 100) === 0, "no discount when price higher");
  // 额外边界测试
  console.assert(discountPct(100) === 0, "no discount when compareAt undefined");
  console.assert(discountPct(100, 0) === 0, "no discount when compareAt 0");
}

function Stars({ value = 5, max = 5 }: { value?: number; max?: number }) {
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: max }).map((_, i) => (
        <Star
          key={i}
          className={`h-4 w-4 ${i < value ? "fill-current text-yellow-500" : "fill-transparent text-gray-300"}`}
        />
      ))}
    </div>
  );
}

function ProductCard({ p, highlightDiscount = false }: { p: Product; highlightDiscount?: boolean }) {
  const pct = discountPct(p.price, p.compareAt);
  return (
    <article className="rounded-2xl bg-white p-4 shadow-md ring-1 ring-black/5 transition hover:shadow-lg">
      <div className="flex gap-4">
        <div className="h-28 w-28 shrink-0 overflow-hidden rounded-xl bg-neutral-100">
          <img src={p.image} alt={p.title} className="h-full w-full object-cover" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="line-clamp-2 text-[16px] font-semibold text-neutral-900">{p.title}</h3>
          <div className="mt-1 flex items-baseline gap-2">
            <div className={`text-xl font-bold ${highlightDiscount ? "text-red-600" : "text-neutral-900"}`}>
              ￥{p.price.toFixed(2)}
            </div>
            {p.compareAt && (
              <div className="text-sm text-neutral-500 line-through">￥{p.compareAt.toFixed(2)}</div>
            )}
            {highlightDiscount && pct > 0 && (
              <span className="ml-1 rounded-full bg-red-50 px-2 py-0.5 text-xs font-semibold text-red-600">
                省{pct}%
              </span>
            )}
          </div>
          {p.sold && <div className="text-xs text-neutral-500">已售 {p.sold}</div>}
          {(p.rating || p.reviews) && (
            <div className="mt-1 flex items-center gap-1 text-neutral-700 text-xs">
              {p.rating && <Stars value={p.rating} />}
              {p.reviews && <span>({p.reviews})</span>}
            </div>
          )}
        </div>
        <button className="ml-2 grid h-10 w-10 place-items-center self-end rounded-full bg-neutral-900 text-white shadow-md hover:bg-neutral-800 active:scale-95">
          <ShoppingCart className="h-5 w-5" />
        </button>
      </div>
    </article>
  );
}

// -------------------- Data --------------------
const GUIDE: Guide = {
  name: "小艺",
  avatar:
    "https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?q=80&w=800&auto=format&fit=crop",
  introShort: "专注奢侈品推荐，用专业眼光帮你挑选心仪好物。",
  domains: ["二手奢侈品包包"],
  styles: ["时尚敏锐", "亲和专业", "高效成交"],
  monthlySales: "3.2K+ 单",
  gmv: "￥3.5M/月",
  positiveRate: "99% 好评",
};

const TAB_LABELS: ReadonlyArray<"她的秒杀商品" | "她的本周推荐"> = [
  "她的秒杀商品",
  "她的本周推荐",
];

// 6 个包包/每个 Tab
const FLASH_DEALS: Product[] = [
  { id: 1, title: "Chanel Classic Flap Small · 黑金", price: 23999, compareAt: 25999, sold: "320+", rating: 5, reviews: 87, image: "https://images.unsplash.com/photo-1618336753974-aae8e04506aa?q=80&w=800&auto=format&fit=crop" },
  { id: 2, title: "Louis Vuitton Pochette Metis · Monogram", price: 13800, compareAt: 14999, sold: "1.1K+", rating: 4, reviews: 201, image: "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?q=80&w=800&auto=format&fit=crop" },
  { id: 3, title: "Gucci Marmont Mini · 象牙白", price: 9800, compareAt: 10800, sold: "890+", rating: 5, reviews: 133, image: "https://images.unsplash.com/photo-1620012253295-8cfc0fbe0ef5?q=80&w=800&auto=format&fit=crop" },
  { id: 4, title: "Dior Caro Small · 黑金", price: 16600, compareAt: 17800, sold: "410+", rating: 5, reviews: 72, image: "https://images.unsplash.com/photo-1605581644385-4f6b7960f422?q=80&w=800&auto=format&fit=crop" },
  { id: 5, title: "Celine Ava Bag · 老花", price: 10500, compareAt: 11800, sold: "530+", rating: 5, reviews: 64, image: "https://images.unsplash.com/photo-1605733517503-3bade9f22108?q=80&w=800&auto=format&fit/crop" },
  { id: 6, title: "Prada Re-Edition 2005 · 黑色尼龙", price: 12500, compareAt: 13500, sold: "640+", rating: 5, reviews: 89, image: "https://images.unsplash.com/photo-1620012252713-1c8adabac2ff?q=80&w=800&auto=format&fit=crop" },
];

const WEEKLY_PICKS: Product[] = [
  { id: 7, title: "Dior Saddle Bag · Oblique", price: 16800, sold: "740+", rating: 5, reviews: 102, image: "https://images.unsplash.com/photo-1597073387936-7c03a2dabc3a?q=80&w=800&auto=format&fit=crop" },
  { id: 8, title: "Chanel 19 Small · 黑金", price: 28900, sold: "260+", rating: 5, reviews: 54, image: "https://images.unsplash.com/photo-1617050352214-f73e34cb3b6e?q=80&w=800&auto=format&fit=crop" },
  { id: 9, title: "Hermès Evelyne TPM · 金棕", price: 35800, sold: "120+", rating: 5, reviews: 33, image: "https://images.unsplash.com/photo-1612392062474-fd2b0b4e4f9b?q=80&w=800&auto=format&fit=crop" },
  { id: 10, title: "Celine Triomphe Teen · 象牙白", price: 11800, sold: "560+", rating: 5, reviews: 66, image: "https://images.unsplash.com/photo-1612367993934-df7b76f0d57f?q=80&w=800&auto=format&fit=crop" },
  { id: 11, title: "LV Alma BB · Damier", price: 11900, sold: "680+", rating: 5, reviews: 88, image: "https://images.unsplash.com/photo-1603297637487-c9c8f0b2a27f?q=80&w=800&auto=format&fit/crop" },
  { id: 12, title: "Gucci Dionysus Small · GG", price: 13200, sold: "450+", rating: 5, reviews: 51, image: "https://images.unsplash.com/photo-1618354691519-25a5b61896dc?q=80&w=800&auto=format&fit=crop" },
];

// 额外断言，确保每个 Tab 恰好 6 个商品
if (typeof window !== "undefined") {
  console.assert(FLASH_DEALS.length === 6, "FLASH_DEALS should be 6");
  console.assert(WEEKLY_PICKS.length === 6, "WEEKLY_PICKS should be 6");
}

// -------------------- App (带顶部切换) --------------------
export default function ShoppingAssistantMobile() {
  // 顶部主导航：guide(导购) / explore(逛逛)
  const [topTab, setTopTab] = useState<"guide" | "explore">("guide");
  const [active, setActive] = useState<"flash" | "weekly">("flash");
  const [view, setView] = useState<"home" | "chat">("home");
  const [prefillMsg, setPrefillMsg] = useState<string>("");
  const products = active === "flash" ? FLASH_DEALS : WEEKLY_PICKS;

  const inputRef = React.useRef<HTMLInputElement | null>(null);
  const handleStartChat = () => setView("chat");
  const handleSendFromHome = () => {
    const text = inputRef.current?.value?.trim();
    if (text) setPrefillMsg(text);
    setView("chat");
  };

  if (view === "chat") return <ShoppingChat onBack={() => setView("home")} prefill={prefillMsg} />;
  if (topTab === "explore") return <ExplorePage onBack={() => setTopTab("guide")} />;

  // 导购页
  return (
    <div className="w-full min-h-screen bg-neutral-100 text-neutral-900">
      {/* 顶部切换条（仿抖音） */}
      <div className="sticky top-0 z-30 w-full bg-black/90 backdrop-blur">
        <div className="mx-auto flex max-w-md items-center justify-between px-4 py-2">
          <div className="flex items-center gap-6 text-white">
            {(["guide", "explore"] as const).map((k) => {
              const label = k === "guide" ? "导购" : "逛逛";
              const activeTop = topTab === k;
              return (
                <button
                  key={k}
                  onClick={() => setTopTab(k)}
                  className={`relative pb-1.5 text-[16px] font-semibold ${activeTop ? "text-white" : "text-white/60"}`}
                >
                  {label}
                  {activeTop && (
                    <span className="absolute -bottom-0.5 left-0 right-0 mx-auto block h-0.5 w-9 rounded bg-white" />
                  )}
                </button>
              );
            })}
          </div>
          <div className="h-6 w-6" />
        </div>
      </div>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-neutral-900" />
        <div className="absolute inset-x-0 -top-40 h-[28rem] bg-gradient-to-b from-neutral-800 via-neutral-900 to-neutral-900 opacity-90" />

        <div className="relative z-10 mx-auto flex max-w-md flex-col items-center px-4 pt-10 pb-6">
          <div className="mx-auto h-36 w-36 overflow-hidden rounded-full border-4 border-neutral-800 shadow-2xl ring-8 ring-black/20">
            <img src={GUIDE.avatar} alt="导购头像" className="h-full w-full object-cover" />
          </div>
          <h1 className="mt-5 text-center text-3xl font-bold text-white">{GUIDE.name}</h1>
          <div className="mt-2 inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-1.5 text-white text-sm backdrop-blur ring-1 ring-white/15">
            <Trophy className="h-4 w-4 text-amber-300" />
            <span>本月最佳AI购物导购</span>
          </div>

          <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
            {GUIDE.domains.map((chip) => (
              <span key={chip} className="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-sm text-white">{chip}</span>
            ))}
          </div>

          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {GUIDE.styles.map((s) => (
              <span key={s} className="rounded-full border border-white/20 bg-white/5 px-3 py-1 text-sm text-white/80">{s}</span>
            ))}
          </div>

          <p className="mt-4 max-w-md text-center text-white/90">{GUIDE.introShort}</p>

          <div className="mt-5 grid w-full max-w-md grid-cols-3 gap-3 text-center text-white">
            <div>
              <div className="text-xs text-white/70">月成交量</div>
              <div className="mt-1 text-lg font-bold">{GUIDE.monthlySales}</div>
            </div>
            <div>
              <div className="text-xs text-white/70">GMV</div>
              <div className="mt-1 text-lg font-bold">{GUIDE.gmv}</div>
            </div>
            <div>
              <div className="text-xs text-white/70">好评率</div>
              <div className="mt-1 text-lg font-bold">{GUIDE.positiveRate}</div>
            </div>
          </div>

          <button
            onClick={handleStartChat}
            className="mt-5 inline-flex items-center gap-2 rounded-full bg-white/90 px-5 py-2 text-[15px] font-semibold text-neutral-900 shadow-lg backdrop-blur transition hover:bg-white"
          >
            <MessageCircle className="h-5 w-5" /> 点击进行对话
          </button>
        </div>
      </section>

      {/* 商品区内 Tabs */}
      <div className="sticky top-[48px] z-20 mx-auto w-full max-w-md bg-neutral-100/95 px-4 pt-3 backdrop-blur">
        <div className="flex gap-6 border-b border-neutral-200 pb-1">
          {TAB_LABELS.map((label, idx) => {
            const isActive = (idx === 0 && active === "flash") || (idx === 1 && active === "weekly");
            return (
              <button
                key={label}
                onClick={() => setActive(idx === 0 ? "flash" : "weekly")}
                className={`relative pb-2 text-[20px] font-bold transition-colors ${isActive ? "text-neutral-900" : "text-neutral-400"}`}
              >
                {label}
                {isActive && (
                  <span className="absolute -bottom-[3px] left-0 right-0 mx-auto block h-1 w-[56px] rounded-full bg-neutral-900" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Products */}
      <div className="mx-auto max-w-md space-y-4 px-4 py-4 pb-28">
        {products.map((p) => (
          <ProductCard key={p.id} p={p} highlightDiscount={active === "flash"} />
        ))}
      </div>

      {/* Floating composer */}
      <div id="composer" className="fixed bottom-4 left-0 right-0 z-30 mx-auto max-w-md px-4">
        <div className="flex items-center gap-2 rounded-full bg-white p-3 shadow-xl ring-1 ring-black/5">
          <div className="grid h-10 w-10 place-items-center rounded-full bg-neutral-900 text-white">
            <Tag className="h-5 w-5" />
          </div>
          <input
            ref={inputRef}
            className="flex-1 bg-transparent text-[15px] outline-none placeholder:text-neutral-400"
            placeholder="和导购说：想要本周推荐里更基础百搭的款…"
          />
          <button onClick={handleSendFromHome} className="grid h-10 w-10 place-items-center rounded-full bg-neutral-900 text-white active:scale-95">
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}

// -------------------- Explore (逛逛) --------------------
function ExplorePage({ onBack }: { onBack: () => void }) {
  const ALL = [...FLASH_DEALS, ...WEEKLY_PICKS];
  const [query, setQuery] = useState("");
  const [analysis, setAnalysis] = useState<{ brands: string[]; colors: string[]; styles: string[]; budget?: number; summary: string; }>({ brands: [], colors: [], styles: [], summary: "" });
  const [results, setResults] = useState<Product[]>(ALL);

  function parseQuery(q: string) {
    const brands = ["chanel", "香奈儿", "lv", "louis vuitton", "dior", "celine", "gucci", "hermès", "prada"].filter(b => q.toLowerCase().includes(b));
    const colorMap = ["黑", "白", "红", "棕", "金", "银", "绿", "蓝"];
    const colors = colorMap.filter(c => q.includes(c));
    const styles = ["腋下", "斜挎", "托特", "经典", "迷你", "老花", "尼龙", "皮"].filter(s => q.includes(s));
    const budgetMatch = q.match(/(\d{3,5})\s*(?:元|rmb|块|人民币)?/i);
    const budget = budgetMatch ? Number(budgetMatch[1]) : undefined;

    const parts: string[] = [];
    if (brands.length) parts.push(`品牌: ${brands.join(" / ")}`);
    if (colors.length) parts.push(`颜色: ${colors.join(" / ")}`);
    if (styles.length) parts.push(`风格: ${styles.join(" / ")}`);
    if (budget) parts.push(`预算 ≤ ${budget}`);
    const summary = parts.length ? parts.join(" · ") : "解析：未识别到特定条件，已展示人气单品";
    return { brands, colors, styles, budget, summary };
  }

  function applyFilters(list: Product[], a: ReturnType<typeof parseQuery>) {
    return list.filter(p => {
      const t = `${p.title}`.toLowerCase();
      if (a.brands.length && !a.brands.some(b => t.includes(b))) return false;
      if (a.colors.length && !a.colors.some(c => p.title.includes(c))) return false;
      if (a.styles.length && !a.styles.some(s => p.title.includes(s))) return false;
      if (a.budget && p.price > a.budget) return false;
      return true;
    });
  }

  function runSearch(text: string) {
    const a = parseQuery(text);
    setAnalysis(a);
    setResults(applyFilters(ALL, a));
  }

  React.useEffect(() => {
    setResults(ALL);
    setAnalysis({ brands: [], colors: [], styles: [], summary: "解析：为你推荐当下人气二手奢品包包" });
  }, []);

  return (
    <div className="w-full min-h-screen bg-neutral-100">
      {/* 顶部切换条（仿抖音） */}
      <div className="sticky top-0 z-30 w-full bg-black/90 backdrop-blur">
        <div className="mx-auto flex max-w-md items-center justify-between px-4 py-2">
          <div className="flex items-center gap-6 text-white">
            {(["guide", "explore"] as const).map((k) => {
              const label = k === "guide" ? "导购" : "逛逛";
              const activeTop = k === "explore";
              return (
                <button key={k} onClick={() => (k === "guide" ? onBack() : null)} className={`relative pb-1.5 text-[16px] font-semibold ${activeTop ? "text-white" : "text-white/60"}`}>
                  {label}
                  {activeTop && <span className="absolute -bottom-0.5 left-0 right-0 mx-auto block h-0.5 w-9 rounded bg-white" />}
                </button>
              );
            })}
          </div>
          <div className="h-6 w-6" />
        </div>
      </div>

      {/* 解析与搜索条 */}
      <div className="mx-auto max-w-md px-4 pt-3">
        <div className="rounded-2xl bg-black text-white px-4 py-3 shadow">
          <div className="text-xs text-white/70">搜索/筛选解析</div>
          <div className="mt-1 text-sm leading-relaxed">{analysis.summary}</div>
        </div>

        <div className="mt-3 flex items-center gap-2 rounded-full bg-white p-3 shadow ring-1 ring-black/5">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && runSearch(query)}
            placeholder="自然语言搜索：想要2万以内、黑色、适合通勤的经典款…"
            className="flex-1 bg-transparent text-[15px] outline-none placeholder:text-neutral-400"
          />
          <button onClick={() => runSearch(query)} className="grid h-10 w-10 place-items-center rounded-full bg-neutral-900 text-white active:scale-95">
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* 瀑布流 */}
      <div className="mx-auto max-w-md px-4 py-4 pb-16">
        <div className="columns-2 gap-3 [column-fill:_balance]">
          {results.map((p) => (
            <div key={p.id} className="mb-3 break-inside-avoid">
              <div className="overflow-hidden rounded-2xl bg-white shadow ring-1 ring-black/5">
                <div className="relative">
                  <img src={p.image} alt={p.title} className="h-auto w-full object-cover" />
                  {p.compareAt && p.compareAt > p.price && (
                    <span className="absolute left-2 top-2 rounded-full bg-red-600/90 px-2 py-0.5 text-xs font-bold text-white">省{discountPct(p.price, p.compareAt)}%</span>
                  )}
                </div>
                <div className="p-3">
                  <div className="line-clamp-2 text-[13px] font-semibold text-neutral-900">{p.title}</div>
                  <div className="mt-1 flex items-baseline gap-1">
                    <span className="text-[15px] font-bold">￥{p.price.toFixed(2)}</span>
                    {p.compareAt && <span className="text-xs text-neutral-400 line-through">￥{p.compareAt.toFixed(2)}</span>}
                  </div>
                  {p.rating && (
                    <div className="mt-1 flex items-center gap-1">
                      <Stars value={p.rating} />
                      {p.reviews && <span className="text-xs text-neutral-500">({p.reviews})</span>}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
        {results.length === 0 && (
          <div className="py-16 text-center text-sm text-neutral-500">未找到匹配结果，试试降低条件或更换关键词～</div>
        )}
      </div>
    </div>
  );
}

// -------------------- Chat Page --------------------
function ShoppingChat({ onBack, prefill = "" }: { onBack: () => void; prefill?: string }) {
  const [messages, setMessages] = useState<Array<{ role: "user" | "agent"; text: string }>>([]);
  const [input, setInput] = useState("");
  const [caption, setCaption] = useState<string>("");
  const [showCaption, setShowCaption] = useState(false);

  React.useEffect(() => {
    if (prefill) {
      setInput(prefill);
      setTimeout(() => send(), 50);
    }
  }, [prefill]);

  // 店铺背景
  const bg = "https://images.unsplash.com/photo-1519741497674-611481863552?q=80&w=1200&auto=format&fit=crop";

  // 字幕：出现并在 2.5s 后淡出
  function pushCaption(text: string) {
    setCaption(text);
    setShowCaption(true);
    setTimeout(() => setShowCaption(false), 2500);
  }

  // Demo 用固定脚本（关键词触发），便于演示
  function scriptedReply(userText: string): string {
    const t = userText.toLowerCase();
    if (t.includes("香奈儿") || t.includes("chanel")) {
      return "这边有一只 Chanel Classic 小号，95新，今日直播间价直降 2,000，支持鉴定～";
    }
    if (t.includes("百搭") || t.includes("入门") || t.includes("日常")) {
      return "想要百搭的话，推荐奶白/黑金、腋下小包或手机包，通勤约会都 OK。";
    }
    if (t.includes("预算") || t.includes("price") || /\b(\d{4,5})\b/.test(t)) {
      return "你的预算大概多少呢？我可以给你做同价位 3 款横评。";
    }
    if (t.includes("保值") || t.includes("转卖") || t.includes("升值")) {
      return "保值首选 Chanel、Hermès 的经典线，LV 老花也很稳，成色越好越保值。";
    }
    if (t.includes("质保") || t.includes("售后") || t.includes("发票")) {
      return "我们提供 7 天无理由 + 1 年质保，支持第三方鉴定和平台担保。";
    }
    if (t.includes("在吗") || t.includes("hello") || t.includes("hi") || t.includes("你好")) {
      return "在的～需要什么风格或场景的包包？我可以先给你几款人气款。";
    }
    return "收到～我再帮你筛选更适合的款式，也可以告诉我你的身高/场景/预算。";
  }

  function send() {
    const text = input.trim();
    if (!text) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");

    setTimeout(() => {
      const reply = scriptedReply(text);
      setMessages((m) => [...m, { role: "agent", text: reply }]);
      pushCaption(reply);
    }, 600);
  }

  return (
    <div className="relative min-h-screen w-full bg-black text-white">
      {/* 背景图 */}
      <img src={bg} alt="store" className="absolute inset-0 h-full w-full object-cover opacity-80" />

      {/* 返回 */}
      <div className="absolute left-3 top-3 z-20">
        <button onClick={onBack} className="rounded-full bg-white/20 px-3 py-1 text-sm backdrop-blur">返回</button>
      </div>

      {/* 顶部小窗（示意） */}
      <div className="absolute left-3 top-16 z-10 overflow-hidden rounded-xl ring-2 ring-white/60">
        <img src={GUIDE.avatar} className="h-20 w-16 object-cover" />
      </div>

      {/* 字幕 */}
      <div className={`pointer-events-none absolute left-5 right-5 top-36 z-10 transition-opacity ${showCaption ? "opacity-100" : "opacity-0"}`}>
        <div className="mx-auto max-w-xs rounded-2xl bg-black/60 px-4 py-2 text-center text-base leading-snug shadow-lg">
          {caption}
        </div>
      </div>

      {/* 聊天消息区 */}
      <div className="absolute inset-x-0 bottom-28 top-24 z-0 overflow-y-auto px-4">
        <div className="mx-auto max-w-md space-y-2">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`${m.role === "user" ? "bg-white text-neutral-900" : "bg-neutral-900/80 text-white"} max-w-[75%] rounded-2xl px-3 py-2 text-sm shadow`}>
                {m.text}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 底部输入区 */}
      <div className="absolute bottom-4 left-0 right-0 z-20 mx-auto max-w-md px-4">
        <div className="flex items-center gap-2 rounded-full bg-white p-3 text-neutral-900 shadow-xl ring-1 ring-black/5">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            className="flex-1 bg-transparent text-[15px] outline-none placeholder:text-neutral-400"
            placeholder="和导购说点什么…"
          />
          <button onClick={send} className="grid h-10 w-10 place-items-center rounded-full bg-neutral-900 text-white active:scale-95">
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
