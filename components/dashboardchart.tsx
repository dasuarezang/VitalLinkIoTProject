"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";

export default function DashboardChart() {
  const [data, setData] = useState([]);

  useEffect(() => {
    const supabase = createClient();

    const fetchData = async () => {
      // Traemos los datos ordenados por fecha
      const { data: rawData, error } = await supabase
        .from("sensor_data")
        .select("frec_cardiaca, created_at")
        .order("created_at", { ascending: true });

      if (!error && rawData) {
        const now = new Date();

        setData(
          rawData.map((item) => {
            const itemDate = new Date(item.created_at);

            const diffMs = itemDate.getTime() - now.getTime();
            const diffMins = Math.round(diffMs / 60000);
            
            return {

              timeLabel: diffMins === 0 ? "Ahora" : `${diffMins} min`,
              frec: item.frec_cardiaca,
              originalTime: item.created_at
            };
          })
        );
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full h-[70vh] flex justify-center">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          
          <XAxis 
            dataKey="timeLabel" 
            angle={-90}
            textAnchor="end"
            height={80}
            interval={0}
            tick={{ fontSize: 12 }}
          />
          
          <YAxis />
          <Tooltip labelStyle={{ color: "black" }} />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="frec" 
            stroke="#8884d8" 
            activeDot={{ r: 8 }} 
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

