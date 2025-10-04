import { Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { DashboardPage } from "./features/dashboard/DashboardPage";
import { FreeAgencyPage } from "./features/freeAgency/FreeAgencyPage";
import { TradeCenterPage } from "./features/trade/TradeCenterPage";
import { DepthChartPage } from "./features/depthChart/DepthChartPage";
import { DataUploadsPage } from "./features/uploads/DataUploadsPage";
import { StandingsPage } from "./features/standings/StandingsPage";
import { ResultsPage } from "./features/results/ResultsPage";

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="results">
          <Route index element={<ResultsPage />} />
          <Route path=":week" element={<ResultsPage />} />
        </Route>
        <Route path="free-agency" element={<FreeAgencyPage />} />
        <Route path="trade-center" element={<TradeCenterPage />} />
        <Route path="depth-chart" element={<DepthChartPage />} />
        <Route path="data-uploads" element={<DataUploadsPage />} />
        <Route path="standings" element={<StandingsPage />} />
      </Route>
    </Routes>
  );
}

export default App;
