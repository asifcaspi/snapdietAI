import React from "react";
import { View, Text, Image, StyleSheet, FlatList, Button } from "react-native";

interface ImageResultDisplayProps {
  imageUri: string;
  results: Record<string, string | null>;
  onReturn: () => void;
}

const ImageResultDisplay: React.FC<ImageResultDisplayProps> = ({ imageUri, results, onReturn }) => {
  return (
    <View style={styles.container}>
      {/* Display the image */}
      <Image source={{ uri: imageUri }} style={styles.image} />

      {/* Display the results */}
      <Text style={styles.resultsTitle}>Results per 100 grams:</Text>
      <FlatList
        data={Object.entries(results)}
        keyExtractor={([key]) => key}
        renderItem={({ item: [key, value] }) => (
          <Text style={styles.resultItem}>
            {key}: {value ?? "N/A"}
          </Text>
        )}
      />
      <Button title="Return to Camera" onPress={onReturn} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginTop: 20,
    alignItems: "center",
  },
  image: {
    width: 200,
    height: 200,
    resizeMode: "contain",
    marginBottom: 20,
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 10,
  },
  resultItem: {
    fontSize: 16,
    marginBottom: 5,
  },
});

export default ImageResultDisplay;