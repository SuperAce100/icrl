# =============================================================================
# Machine Learning Basics in R: A Complete Walkthrough
# =============================================================================
# We'll build a decision tree to classify iris flowers by species
# and explain ML concepts as they arise naturally in the workflow.

# -----------------------------------------------------------------------------
# STEP 1: Load Libraries
# -----------------------------------------------------------------------------
# Install packages if needed (uncomment if first time):
# install.packages(c("rpart", "rpart.plot", "caret"))

library(rpart)       # For decision trees
library(rpart.plot)  # For visualizing trees
library(caret)       # For ML utilities (train/test split, evaluation)

# -----------------------------------------------------------------------------
# STEP 2: Load and Explore the Data
# -----------------------------------------------------------------------------
# The iris dataset is built into R - 150 flowers, 3 species

data(iris)

cat("=== UNDERSTANDING YOUR DATA ===\n\n")

# First look at the structure
cat("Dataset dimensions:", nrow(iris), "rows x", ncol(iris), "columns\n\n")

cat("First 6 rows:\n")
print(head(iris))

cat("\nColumn types:\n")
str(iris)

cat("\nStatistical summary:\n")
print(summary(iris))

# KEY ML CONCEPT: Features vs Target
# ----------------------------------
# Features (X): The input variables used to make predictions
#   - Sepal.Length, Sepal.Width, Petal.Length, Petal.Width
# Target (y): What we're trying to predict
#   - Species (setosa, versicolor, virginica)

cat("\n=== ML CONCEPT: Features vs Target ===\n")
cat("Features (inputs):", paste(names(iris)[1:4], collapse=", "), "\n")
cat("Target (output):", names(iris)[5], "\n")
cat("Target classes:", paste(levels(iris$Species), collapse=", "), "\n")

# -----------------------------------------------------------------------------
# STEP 3: Split Data into Training and Test Sets
# -----------------------------------------------------------------------------
# KEY ML CONCEPT: Train/Test Split
# ---------------------------------
# Why split? We need to evaluate our model on data it has NEVER seen.
# - Training set: Used to teach the model patterns
# - Test set: Used to evaluate how well it generalizes to new data
# 
# If we tested on training data, we'd get overly optimistic results
# (like grading a student on questions they've already seen!)

cat("\n=== ML CONCEPT: Train/Test Split ===\n")

set.seed(42)  # For reproducibility (same "random" split each time)

# Create index for 80% training, 20% testing
train_index <- createDataPartition(iris$Species, p = 0.8, list = FALSE)

train_data <- iris[train_index, ]
test_data  <- iris[-train_index, ]

cat("Training set:", nrow(train_data), "samples (80%)\n")
cat("Test set:", nrow(test_data), "samples (20%)\n")

# Check that classes are balanced in both sets
cat("\nClass distribution in training set:\n")
print(table(train_data$Species))

cat("\nClass distribution in test set:\n")
print(table(test_data$Species))

# -----------------------------------------------------------------------------
# STEP 4: Train a Decision Tree Model
# -----------------------------------------------------------------------------
# KEY ML CONCEPT: The Learning Algorithm
# ---------------------------------------
# A decision tree learns by finding the best questions to ask about the data.
# It recursively splits the data based on feature values that best separate
# the target classes.
#
# Example: "Is Petal.Length < 2.5?" -> If yes, probably setosa!

cat("\n=== TRAINING THE MODEL ===\n")

# Train the decision tree
# Formula: Species ~ . means "predict Species using all other columns"
model <- rpart(
  formula = Species ~ .,
  data = train_data,
  method = "class"  # Classification (not regression)
)

cat("Model trained successfully!\n\n")

# View the decision rules the model learned
cat("Decision rules learned:\n")
print(model)

# -----------------------------------------------------------------------------
# STEP 5: Visualize the Model
# -----------------------------------------------------------------------------
# One advantage of decision trees: they're interpretable!

cat("\n=== MODEL VISUALIZATION ===\n")
cat("Saving decision tree plot to 'decision_tree.png'...\n")

png("decision_tree.png", width = 800, height = 600)
rpart.plot(
  model,
  main = "Iris Species Classification Tree",
  extra = 104,  # Show probability and percentage
  under = TRUE,
  faclen = 0    # Don't abbreviate factor levels
)
dev.off()

cat("Tree visualization saved!\n")

# -----------------------------------------------------------------------------
# STEP 6: Make Predictions
# -----------------------------------------------------------------------------
# KEY ML CONCEPT: Inference/Prediction
# -------------------------------------
# Once trained, we use the model to predict on new, unseen data.
# The model applies its learned rules to classify each sample.

cat("\n=== MAKING PREDICTIONS ===\n")

# Predict on test set
predictions <- predict(model, test_data, type = "class")

# Show some predictions vs actual values
comparison <- data.frame(
  Actual = test_data$Species,
  Predicted = predictions,
  Correct = test_data$Species == predictions
)

cat("Sample predictions (first 10):\n")
print(head(comparison, 10))

# -----------------------------------------------------------------------------
# STEP 7: Evaluate Model Performance
# -----------------------------------------------------------------------------
# KEY ML CONCEPT: Model Evaluation Metrics
# ----------------------------------------
# How do we know if our model is good? We use metrics:
#
# - Accuracy: % of correct predictions (simple but can be misleading)
# - Confusion Matrix: Shows what types of errors the model makes
# - Precision: Of predicted positives, how many were correct?
# - Recall: Of actual positives, how many did we find?

cat("\n=== MODEL EVALUATION ===\n")

# Confusion Matrix
cat("Confusion Matrix:\n")
conf_matrix <- confusionMatrix(predictions, test_data$Species)
print(conf_matrix$table)

# Accuracy
cat("\nOverall Accuracy:", round(conf_matrix$overall["Accuracy"] * 100, 2), "%\n")

# Per-class statistics
cat("\nPer-class Performance:\n")
print(round(conf_matrix$byClass[, c("Sensitivity", "Specificity", "Precision")], 3))

# -----------------------------------------------------------------------------
# STEP 8: Understanding Overfitting vs Underfitting
# -----------------------------------------------------------------------------
# KEY ML CONCEPT: The Bias-Variance Tradeoff
# -------------------------------------------
# - Underfitting (high bias): Model too simple, misses patterns
# - Overfitting (high variance): Model too complex, memorizes noise
# - Goal: Find the sweet spot that generalizes well

cat("\n=== OVERFITTING DEMONSTRATION ===\n")

# Train an overly complex tree (no pruning)
overfit_model <- rpart(
  Species ~ .,
  data = train_data,
  method = "class",
  control = rpart.control(minsplit = 2, cp = 0)  # Very complex tree
)

# Compare training vs test accuracy
train_pred_simple <- predict(model, train_data, type = "class")
test_pred_simple <- predict(model, test_data, type = "class")

train_pred_complex <- predict(overfit_model, train_data, type = "class")
test_pred_complex <- predict(overfit_model, test_data, type = "class")

cat("Simple Model:\n")
cat("  Training Accuracy:", round(mean(train_pred_simple == train_data$Species) * 100, 2), "%\n")
cat("  Test Accuracy:    ", round(mean(test_pred_simple == test_data$Species) * 100, 2), "%\n")

cat("\nComplex Model (potential overfit):\n")
cat("  Training Accuracy:", round(mean(train_pred_complex == train_data$Species) * 100, 2), "%\n")
cat("  Test Accuracy:    ", round(mean(test_pred_complex == test_data$Species) * 100, 2), "%\n")

cat("\nNote: If training >> test accuracy, the model is overfitting!\n")

# -----------------------------------------------------------------------------
# STEP 9: Feature Importance
# -----------------------------------------------------------------------------
# KEY ML CONCEPT: Which Features Matter?
# --------------------------------------
# Not all features contribute equally. Understanding importance helps with:
# - Feature selection (removing useless features)
# - Domain understanding (what drives predictions?)

cat("\n=== FEATURE IMPORTANCE ===\n")

importance <- model$variable.importance
importance_df <- data.frame(
  Feature = names(importance),
  Importance = as.numeric(importance)
)
importance_df <- importance_df[order(-importance_df$Importance), ]

cat("Feature importance (higher = more predictive):\n")
print(importance_df, row.names = FALSE)

# -----------------------------------------------------------------------------
# STEP 10: Making Predictions on New Data
# -----------------------------------------------------------------------------
cat("\n=== PREDICTING NEW FLOWERS ===\n")

# Simulate a new flower measurement
new_flower <- data.frame(
  Sepal.Length = 5.0,
  Sepal.Width = 3.5,
  Petal.Length = 1.5,
  Petal.Width = 0.3
)

cat("New flower measurements:\n")
print(new_flower)

# Get prediction and probabilities
prediction <- predict(model, new_flower, type = "class")
probabilities <- predict(model, new_flower, type = "prob")

cat("\nPredicted species:", as.character(prediction), "\n")
cat("Confidence (probabilities):\n")
print(round(probabilities, 3))

# -----------------------------------------------------------------------------
# SUMMARY: The ML Workflow
# -----------------------------------------------------------------------------
cat("\n")
cat("=============================================================================\n")
cat("                    MACHINE LEARNING WORKFLOW SUMMARY                        \n")
cat("=============================================================================\n")
cat("
1. COLLECT & EXPLORE DATA
   - Understand your features and target
   - Check for missing values, outliers, class imbalance

2. PREPARE DATA  
   - Split into training and test sets
   - (Optional) Feature scaling, encoding, selection

3. CHOOSE & TRAIN MODEL
   - Select algorithm (decision tree, random forest, SVM, etc.)
   - Fit model on training data

4. EVALUATE MODEL
   - Predict on test set
   - Calculate metrics (accuracy, precision, recall, F1)
   - Check for overfitting

5. TUNE & IMPROVE
   - Adjust hyperparameters
   - Try different algorithms
   - Add/remove features

6. DEPLOY
   - Use model to predict on new, real-world data
")

cat("\n=== Script complete! Check 'decision_tree.png' for visualization ===\n")
