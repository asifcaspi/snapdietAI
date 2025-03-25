import { SafeAreaView } from "react-native";
import FoodCamera from "./components/FoodCamera";

export default function App() {
  return (
    <SafeAreaView style={{ flex: 1 }}>
      <FoodCamera />
    </SafeAreaView>
  );
}