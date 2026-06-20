import json
import numpy as np # for mean, median, arrays
import matplotlib.pyplot as plt # for graphs, visualizations of distributions
from collections import defaultdict, Counter # special dictionaries

plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 6)

# data loading function
def load_sessions(filepath):
    sessions = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                sessions.append(json.loads(line))
    return sessions

# train/test split function
def train_test_split(sessions):
    train_sessions = [session[:-1] for session in sessions]
    test_targets = [session[-1] for session in sessions]
    return train_sessions, test_targets


# building transition graph
def build_transition_graph(train_sessions):
    transitions = defaultdict(lambda: defaultdict(int)) # Creates a dictionary where each value is another dictionary with default value 0
    # Allows writing transitions[380][293] += 1, even if keys didn't exist
    out_counts = defaultdict(int)
    for session in train_sessions:
        for i in range(len(session) - 1):
            current = session[i]
            next_item = session[i + 1]
            transitions[current][next_item] += 1 # Increments transition counter current -> next_item
            out_counts[current] += 1
    return transitions, out_counts


#calculating transition probabilities
def compute_transition_probs(transitions, out_counts):
    probs = {}
    for i, next_dict in transitions.items(): # i - current product, next_dict - all transitions from it
        total = out_counts[i]
        probs[i] = {}
        for j, cnt in next_dict.items(): # j - next product, cnt - how many times the transition occurred
            probs[i][j] = cnt / total # probability = number of transitions / total number of outcomes
    return probs


# fallback
def get_incoming_popularity(transitions):
    incoming = defaultdict(int)
    for current, next_dict in transitions.items(): # Iterate over all transitions
        for next_item, count in next_dict.items(): # Iterate over all recipients of the transition
            incoming[next_item] += count
    return incoming


# recommendation model
def recommend_next_items(last_item, transition_probs, top_k=10, fallback_top_items=None): # fallback for unknown product
    if fallback_top_items is None:
        fallback_top_items = [] # creates empty list (to avoid errors)

    if last_item in transition_probs and transition_probs[last_item]: # check if we know this product and if it has transitions
        candidates = sorted(transition_probs[last_item].items(), key=lambda x: -x[1])
        recommendations = [item for item, prob in candidates[:top_k]] # take only product IDs (without probabilities), first top_k
    else:
        recommendations = fallback_top_items[:top_k]

    recommendations = [r for r in recommendations if r != last_item] # remove last_item itself (pointless to recommend what's already being viewed)

    if len(recommendations) < top_k and fallback_top_items:
        for item in fallback_top_items: # iterate through fallback
            if item not in recommendations and item != last_item:
                recommendations.append(item)
            if len(recommendations) == top_k:
                break

    return recommendations[:top_k]

# hit@k metric
def hit_at_k(recommendations, true_items, k=10):
    assert len(recommendations) == len(true_items), \
        "recommendations and true_items must have the same length"
    hits = 0
    for recs, true_item in zip(recommendations, true_items): # iterate in pairs (recommendations for example i, true answer for example i)
        if true_item in recs[:k]:
            hits += 1
    return hits / len(true_items) if true_items else 0 # returns hit rate (0 to 1)


# main

# Load data
sessions = load_sessions('sessions.jsonl')
print(f"Loaded sessions: {len(sessions)}")

# Basic statistics
all_items = [item for session in sessions for item in session] # flatten all sessions into one list
unique_items = set(all_items)
lengths = [len(session) for session in sessions]


# Step 1 Data analysis
print("\n" + "-" * 15)
print("DATA ANALYSIS")
print("-" * 15)
print(f"Unique products: {len(unique_items)}")
print(f"Total interactions: {len(all_items)}")
print(f"Average session length: {np.mean(lengths):.2f}")

# Graph 1: session length distribution
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4))

ax1.hist(lengths, bins=30, edgecolor='black', alpha=0.7, color='seagreen') # histogram with 30 bins, black border, 0.7 transparency, steel blue color
ax1.set_xlabel('Session length (number of products)')
ax1.set_ylabel('Frequency')
ax1.set_title('Session Length Distribution')
ax1.axvline(np.mean(lengths), color='red', linestyle='--', label=f'Mean = {np.mean(lengths):.1f}')
ax1.axvline(np.median(lengths), color='green', linestyle='--', label=f'Median = {np.median(lengths):.1f}')
ax1.legend()

ax2.hist(lengths, bins=50, edgecolor='black', alpha=0.7, color='seagreen', log=True)
ax2.set_xlabel('Session length (number of products)')
ax2.set_ylabel('Frequency (log scale)')
ax2.set_title('Session Length Distribution (log scale)')

plt.tight_layout()
plt.show()

# Graph 2
item_counts = Counter(all_items)
top_items = item_counts.most_common(20)

fig, ax = plt.subplots(figsize=(14, 6))
top_items_plot = top_items[::-1]
ax.barh([str(x[0]) for x in top_items_plot], [x[1] for x in top_items_plot], color='darkgreen')
ax.set_xlabel('Frequency')
ax.set_ylabel('Product ID')
ax.set_title('Top-20 Most Popular Products')
plt.tight_layout()
plt.show()

print("\nTop-5 products by frequency:")
for item_id, count in top_items[:5]:
    print(f"   Product {item_id}: {count} times")

# Rare items
rare_items = [item for item, count in item_counts.items() if count == 1]
print(f"\nRare items (appear once): {len(rare_items)}")
print(f"   Percentage of all unique products: {len(rare_items) / len(unique_items) * 100:.1f}%")

# Sessions with duplicate products
duplicate_in_session = 0
for session in sessions:
    if len(session) != len(set(session)):
        duplicate_in_session += 1
print(f"\nSessions with duplicate products: {duplicate_in_session} ({duplicate_in_session / len(sessions) * 100:.1f}%)")

print("\n" + "-" * 15)
print("OBSERVATIONS")
print("-" * 15)
print("Sessions with consecutive duplicate products exist")
print("Session lengths range from 3 to 20, averaging 10.5 with a median of 9.0")
print("Rare items constitute {:.1f}%".format(len(rare_items) / len(unique_items) * 100))
print("Number of unique products: {}".format(len(unique_items)))

# Step 2 Train/test split
train_sessions, test_targets = train_test_split(sessions)

print("\nTrain/Test Split completed")
print(f"   Number of training sequences: {len(train_sessions)}")
print(f"   Number of test targets: {len(test_targets)}")

#Step 3 Transition graph
# Build graph
transitions, out_counts = build_transition_graph(train_sessions)
transition_probs = compute_transition_probs(transitions, out_counts)

#Step 4 Recommendation model
# Fallback: incoming popularity
incoming_counts = get_incoming_popularity(transitions)
fallback_incoming_items = [item for item, _ in sorted(incoming_counts.items(), key=lambda x: -x[1])[:20]]

all_recommendations = []
for train_session in train_sessions:
    if len(train_session) == 0:
        recs = fallback_incoming_items[:10]
    else:
        last_item = train_session[-1]
        recs = recommend_next_items(last_item, transition_probs, 10, fallback_incoming_items)
    all_recommendations.append(recs)

# Step 5 Model evaluation
hit_rate_model = hit_at_k(all_recommendations, test_targets, k=10)
print(f"\nHit@10 of model (with improved fallback): {hit_rate_model:.4f} ({hit_rate_model * 100:.2f}%)")

# Baseline
train_all_items = [item for session in train_sessions for item in session]
old_top_popular = [item for item, cnt in Counter(train_all_items).most_common(10)]
baseline_recommendations = [old_top_popular[:10] for _ in test_targets]
hit_rate_baseline = hit_at_k(baseline_recommendations, test_targets, k=10)
print(f"Hit@10 of baseline (simple popularity top): {hit_rate_baseline:.4f} ({hit_rate_baseline * 100:.2f}%)")

# Comparison
print("\n" + "-" * 15)
print("MODEL COMPARISON")
print("-" * 15)
print(f"Model (graph + fallback): {hit_rate_model:.4f}")
print(f"Baseline (simple popularity top): {hit_rate_baseline:.4f}")
print(f"Difference: {hit_rate_model - hit_rate_baseline:+.4f}")

if hit_rate_model > hit_rate_baseline:
    print("Model outperforms baseline")
else:
    print("Model does not outperform baseline")

# Coverage
visible_targets = 0
for train_session, true_item in zip(train_sessions, test_targets):
    last_item = train_session[-1] if train_session else None
    if last_item is not None and last_item in transition_probs and true_item in transition_probs.get(last_item, {}):
        visible_targets += 1

coverage = visible_targets / len(test_targets) if len(test_targets) > 0 else 0
print(f"\nProportion of test examples where transition (last_item -> true_item) was seen in training: {coverage:.4f}")

