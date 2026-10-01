import { createClient } from "@/lib/supabase/server";
import DashboardChart from "./dashboardchart";

export default async function ChartLoader() {
  const supabase = await createClient();

  const { data, error } = await supabase
    .from("sensor_data")
    .select("frec_cardiaca, created_at")
    .order("created_at", { ascending: true });

  if (error) {
    console.error("Supabase Error:", error);
    return <div className="text-red-500">Error loading data</div>;
  }

  return <DashboardChart data={data || []} />;
}