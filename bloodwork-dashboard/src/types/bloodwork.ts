// exactly mirrors one item from the API response array
export interface BloodworkResult {
  patient_name: string;
  reference_range: string;
  test_name: string;
  time: string;
  unit: string;
  value: number;
}

// the full API response shape
export interface BloodworkResponse {
  start_date: string;
  end_date: string;
  test_names: string[] | null;
  results: BloodworkResult[];
}

// a single time series point after we process the raw data
export interface DataPoint {
  time: string;
  value: number;
}

// one marker grouped with all its data points
export interface Marker {
  test_name: string;
  unit: string;
  reference_range: string;
  data: DataPoint[];
}

// a marker group as shown in the sidebar
export interface MarkerGroup {
  name: string;
  markers: Marker[];
}

// one chart card on the dashboard: one or more series sharing a chart
export interface Panel {
  id: string;
  title: string;
  series: Marker[];
}

// what the user has chosen in the sidebar
export interface Layout {
  selected: string[];
  groupInOne: Record<string, boolean>;
}
