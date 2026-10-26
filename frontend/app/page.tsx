"use client";

import { useMemo, useState } from "react";
import type { FormEvent } from "react";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:4000/api").replace(/\/$/, "");

type Segment = {
  carrierCode?: string;
  carrierName?: string;
  flightNumber?: string;
  departure?: { iataCode?: string; at?: string };
  arrival?: { iataCode?: string; at?: string };
  duration?: string;
};

type Itinerary = {
  duration?: string;
  stops?: number;
  segments?: Segment[];
};

type Flight = {
  id?: string;
  price?: { currency?: string; total?: string };
  validatingAirlineCodes?: string[];
  itineraries?: Itinerary[];
};

type SearchResponse = {
  flights: Flight[];
  count: number;
  currency?: string;
};

function dateAfter(days: number) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatTime(value?: string) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit" }).format(date);
}

function formatDuration(value?: string) {
  const match = value?.match(/PT(?:(\d+)H)?(?:(\d+)M)?/);
  if (!match) return value || "Duration unavailable";
  const hours = match[1] ? `${match[1]}h` : "";
  const minutes = match[2] ? `${match[2]}m` : "";
  return [hours, minutes].filter(Boolean).join(" ") || "—";
}

function money(amount?: string, currency = "USD") {
  const value = Number(amount);
  if (!Number.isFinite(value)) return "Price unavailable";
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(value);
  } catch {
    return `${currency} ${value.toFixed(0)}`;
  }
}

function AirportInput({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <label className="flex min-w-0 flex-col gap-2">
      <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">{label}</span>
      <input
        required
        aria-label={label}
        autoCapitalize="characters"
        maxLength={3}
        minLength={3}
        pattern="[A-Za-z]{3}"
        placeholder={placeholder}
        value={value}
        onChange={(event) => onChange(event.target.value.toUpperCase().replace(/[^A-Z]/g, ""))}
        className="w-full border-0 bg-transparent p-0 text-2xl font-semibold tracking-wide text-slate-900 outline-none placeholder:text-slate-300 focus:ring-0"
      />
      <span className="text-xs text-slate-400">3-letter airport code</span>
    </label>
  );
}

function FlightCard({ flight, index, currency }: { flight: Flight; index: number; currency: string }) {
  const outbound = flight.itineraries?.[0];
  const firstSegment = outbound?.segments?.[0];
  const lastSegment = outbound?.segments?.at(-1);
  const airline = firstSegment?.carrierName || firstSegment?.carrierCode || "Airline";
  const airlineCode = flight.validatingAirlineCodes?.[0] || firstSegment?.carrierCode || "✈";
  const stopCount = outbound?.stops ?? Math.max((outbound?.segments?.length ?? 1) - 1, 0);

  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_8px_30px_rgba(15,23,42,0.04)]">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 px-5 py-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-50 text-xs font-black text-indigo-700">
            {airlineCode}
          </div>
          <div>
            <p className="font-semibold text-slate-900">{airline}</p>
            <p className="text-xs text-slate-500">{firstSegment?.flightNumber ? `Flight ${firstSegment.flightNumber}` : `Option ${index + 1}`}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold tracking-tight text-slate-950">
            {money(flight.price?.total, flight.price?.currency || currency)}
          </p>
          <p className="text-xs text-slate-500">total for your travelers · test fare</p>
        </div>
      </div>

      <div className="grid gap-5 px-5 py-5 sm:grid-cols-[1fr_auto_1fr] sm:items-center sm:px-6">
        <div>
          <p className="text-2xl font-semibold text-slate-900">{formatTime(firstSegment?.departure?.at)}</p>
          <p className="mt-1 text-sm font-medium text-slate-600">{firstSegment?.departure?.iataCode || "—"}</p>
        </div>
        <div className="flex items-center gap-3 text-center text-xs text-slate-500">
          <span className="h-px flex-1 bg-slate-200 sm:w-12 sm:flex-none" />
          <div className="min-w-20">
            <p>{formatDuration(outbound?.duration)}</p>
            <p className="mt-1 font-medium text-slate-700">
              {stopCount === 0 ? "Nonstop" : `${stopCount} stop${stopCount === 1 ? "" : "s"}`}
            </p>
          </div>
          <span className="h-px flex-1 bg-slate-200 sm:w-12 sm:flex-none" />
        </div>
        <div className="sm:text-right">
          <p className="text-2xl font-semibold text-slate-900">{formatTime(lastSegment?.arrival?.at)}</p>
          <p className="mt-1 text-sm font-medium text-slate-600">{lastSegment?.arrival?.iataCode || "—"}</p>
        </div>
      </div>

      {flight.itineraries && flight.itineraries.length > 1 && (
        <div className="border-t border-slate-100 bg-slate-50 px-5 py-3 text-sm text-slate-600 sm:px-6">
          Return flight: {flight.itineraries[1].segments?.[0]?.departure?.iataCode || "—"} → {flight.itineraries[1].segments?.at(-1)?.arrival?.iataCode || "—"}
          <span className="ml-2 text-slate-400">· {formatDuration(flight.itineraries[1].duration)}</span>
        </div>
      )}
    </article>
  );
}

export default function Home() {
  const today = useMemo(() => dateAfter(0), []);
  const [tripType, setTripType] = useState<"round-trip" | "one-way">("round-trip");
  const [origin, setOrigin] = useState("LHR");
  const [destination, setDestination] = useState("DXB");
  const [departureDate, setDepartureDate] = useState(dateAfter(30));
  const [returnDate, setReturnDate] = useState(dateAfter(37));
  const [adults, setAdults] = useState(1);
  const [children, setChildren] = useState(0);
  const [nonStop, setNonStop] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [searchedRoute, setSearchedRoute] = useState("");

  async function searchFlights(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResults(null);

    if (origin === destination) {
      setError("Choose two different airports for your trip.");
      return;
    }
    if (adults + children > 9) {
      setError("This search supports up to 9 travelers. Please adjust the passenger count.");
      return;
    }
    if (tripType === "round-trip" && returnDate <= departureDate) {
      setError("Your return date needs to be after your departure date.");
      return;
    }

    const query = new URLSearchParams({
      from: origin,
      to: destination,
      date: departureDate,
      adults: String(adults),
      children: String(children),
      nonStop: String(nonStop),
      max: "20",
    });
    if (tripType === "round-trip") query.set("returnDate", returnDate);

    setLoading(true);
    setSearchedRoute(`${origin} → ${destination}`);
    try {
      const response = await fetch(`${API_URL}/flights/search?${query.toString()}`);
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = body.detail ?? body.error;
        throw new Error(typeof detail === "string" ? detail : "Flight search failed. Please try again.");
      }
      setResults(body as SearchResponse);
    } catch (searchError) {
      setError(
        searchError instanceof Error
          ? searchError.message
          : "Could not reach VoyageIQ. Make sure the backend is running at localhost:4000.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f5f6fa] text-slate-900">
      <header className="border-b border-slate-200/80 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
          <a href="#top" className="flex items-center gap-2.5" aria-label="VoyageIQ home">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-700 text-lg text-white">✦</span>
            <span className="text-lg font-bold tracking-tight">Voyage<span className="text-indigo-700">IQ</span></span>
          </a>
          <div className="flex items-center gap-3">
            <span className="hidden rounded-full bg-amber-50 px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.12em] text-amber-800 sm:inline-flex">Test flight data</span>
            <a href="#search" className="rounded-full bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700">Search flights</a>
          </div>
        </div>
      </header>

      <section id="top" className="relative overflow-hidden bg-[#101b38]">
        <div className="pointer-events-none absolute -right-20 -top-36 h-[27rem] w-[27rem] rounded-full border border-white/10" />
        <div className="pointer-events-none absolute -right-5 -top-20 h-[20rem] w-[20rem] rounded-full border border-white/10" />
        <div className="mx-auto max-w-7xl px-5 pb-36 pt-16 sm:px-8 sm:pb-40 sm:pt-20">
          <p className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1.5 text-xs font-medium text-indigo-100">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> Your next trip starts here
          </p>
          <h1 className="max-w-2xl text-4xl font-semibold leading-[1.08] tracking-tight text-white sm:text-6xl">
            The journey is part of the <span className="text-[#aebeff]">destination.</span>
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-slate-300 sm:text-lg">
            Search flight options and start shaping a trip that feels like yours.
          </p>
        </div>
      </section>

      <section id="search" className="mx-auto -mt-24 max-w-7xl px-5 pb-16 sm:px-8">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_24px_80px_rgba(15,23,42,0.14)] sm:p-8">
          <div className="mb-7 flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-indigo-700">FLIGHT SEARCH</p>
              <h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">Where do you want to go?</h2>
            </div>
            <div className="flex rounded-full bg-slate-100 p-1" aria-label="Trip type">
              {(["round-trip", "one-way"] as const).map((type) => (
                <button
                  key={type}
                  type="button"
                  aria-pressed={tripType === type}
                  onClick={() => setTripType(type)}
                  className={`rounded-full px-4 py-2 text-sm font-medium capitalize transition ${tripType === type ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-800"}`}
                >
                  {type.replace("-", " ")}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={searchFlights}>
            <div className={`grid gap-3 ${tripType === "round-trip" ? "lg:grid-cols-[1fr_1fr_1fr_1fr]" : "lg:grid-cols-[1.25fr_1fr_1fr]"}`}>
              <div className="relative grid grid-cols-2 gap-4 rounded-2xl border border-slate-200 p-4 focus-within:border-indigo-400 focus-within:ring-4 focus-within:ring-indigo-50">
                <AirportInput label="From" value={origin} onChange={setOrigin} placeholder="LHR" />
                <span className="absolute left-1/2 top-1/2 z-10 flex h-9 w-9 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-sm" aria-hidden="true">⇄</span>
                <AirportInput label="To" value={destination} onChange={setDestination} placeholder="DXB" />
              </div>
              <label className="flex flex-col gap-2 rounded-2xl border border-slate-200 p-4 focus-within:border-indigo-400 focus-within:ring-4 focus-within:ring-indigo-50">
                <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Departure</span>
                <input required type="date" min={today} value={departureDate} onChange={(event) => setDepartureDate(event.target.value)} className="min-h-8 w-full bg-transparent text-base font-semibold text-slate-900 outline-none" />
                <span className="text-xs text-slate-400">Choose your travel date</span>
              </label>
              {tripType === "round-trip" ? (
                <label className="flex flex-col gap-2 rounded-2xl border border-slate-200 p-4 focus-within:border-indigo-400 focus-within:ring-4 focus-within:ring-indigo-50">
                  <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Return</span>
                  <input required type="date" min={departureDate || today} value={returnDate} onChange={(event) => setReturnDate(event.target.value)} className="min-h-8 w-full bg-transparent text-base font-semibold text-slate-900 outline-none" />
                  <span className="text-xs text-slate-400">When will you come back?</span>
                </label>
              ) : (
                <label className="flex flex-col gap-2 rounded-2xl border border-slate-200 p-4 focus-within:border-indigo-400 focus-within:ring-4 focus-within:ring-indigo-50">
                  <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Travelers</span>
                  <select value={adults} onChange={(event) => setAdults(Number(event.target.value))} className="min-h-8 bg-transparent text-base font-semibold text-slate-900 outline-none">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((count) => <option key={count} value={count}>{count} adult{count === 1 ? "" : "s"}</option>)}
                  </select>
                  <span className="text-xs text-slate-400">Select the number of adults</span>
                </label>
              )}
              {tripType === "round-trip" && (
                <label className="flex flex-col gap-2 rounded-2xl border border-slate-200 p-4 focus-within:border-indigo-400 focus-within:ring-4 focus-within:ring-indigo-50">
                  <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Adults</span>
                  <select value={adults} onChange={(event) => setAdults(Number(event.target.value))} className="min-h-8 bg-transparent text-base font-semibold text-slate-900 outline-none">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((count) => <option key={count} value={count}>{count} adult{count === 1 ? "" : "s"}</option>)}
                  </select>
                  <span className="text-xs text-slate-400">At least one adult required</span>
                </label>
              )}
            </div>

            <div className="mt-4 flex flex-wrap items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-slate-600">
                  <span className="font-medium">Children</span>
                  <select value={children} onChange={(event) => setChildren(Number(event.target.value))} className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-sm font-semibold text-slate-900 outline-none focus:border-indigo-400">
                    {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((count) => <option key={count} value={count}>{count}</option>)}
                  </select>
                </label>
                <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-600">
                  <input type="checkbox" checked={nonStop} onChange={(event) => setNonStop(event.target.checked)} className="h-4 w-4 rounded border-slate-300 accent-indigo-700" />
                  Nonstop only
                </label>
              </div>
              <button type="submit" disabled={loading} className="inline-flex min-w-48 items-center justify-center gap-2 rounded-xl bg-indigo-700 px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-indigo-700/20 transition hover:bg-indigo-800 disabled:cursor-wait disabled:opacity-70">
                {loading ? <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" /> Searching…</> : <>Search flights <span aria-hidden="true">→</span></>}
              </button>
            </div>
          </form>

          {error && (
            <div role="alert" className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
              <span className="font-semibold">Search couldn’t be completed.</span> {error}
            </div>
          )}
        </div>

        {results && (
          <section aria-live="polite" className="mt-9">
            <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-slate-500">{searchedRoute}</p>
                <h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">
                  {results.count} flight option{results.count === 1 ? "" : "s"}
                </h2>
              </div>
              <span className="rounded-full bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-800">Simulated test results</span>
            </div>
            {results.flights.length > 0 ? (
              <div className="space-y-3">
                {results.flights.map((flight, index) => <FlightCard key={flight.id || index} flight={flight} index={index} currency={results.currency || "USD"} />)}
              </div>
            ) : (
              <div className="rounded-2xl border border-slate-200 bg-white px-6 py-10 text-center">
                <p className="text-lg font-semibold text-slate-900">No test offers for this search</p>
                <p className="mt-2 text-sm text-slate-500">The sandbox has limited, simulated flight data. Try another route or date.</p>
              </div>
            )}
          </section>
        )}

        {!results && !error && !loading && (
          <p className="mt-5 text-center text-xs leading-5 text-slate-400">
            Flight schedules and prices shown here come from Duffel test mode and are for development only.
          </p>
        )}
      </section>
    </main>
  );
}
