import React from "react";
import { SafeAreaView, View, Image, Text, StyleSheet } from "react-native";
import FoodCamera from "./components/FoodCamera";

export default function App() {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.logoContainer}>
        <Image source={require("./assets/logo.png")} style={styles.logo} />
        <Text style={styles.title}>SnapDietAI</Text>
      </View>
      <FoodCamera />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#f8f9fa",
  },
  logoContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 20,
  },
  logo: {
    width: 70,
    height: 70,
    resizeMode: "contain",
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#2c3e50",
  },
});
