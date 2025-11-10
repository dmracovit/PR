# Lab 3: Memory Scramble - Multiplayer Card Matching Game

**Student Name:** Racovitsa Dumitru  
**Group:** FAF-233  
**Date:** November 2025

---

## Overview

Memory Scramble is a concurrent multiplayer web-based card matching game. Multiple players can simultaneously interact with a shared game board, flipping cards to find matching pairs. The system handles complex race conditions and implements a sophisticated waiting mechanism to ensure game state consistency.

---

## Part 1: System Architecture

### 1.1 Core Components

The application follows a layered architecture with clear separation of concerns:

**Board ADT (`src/board.ts`):**
- Core game logic and state management
- Handles card flipping, matching, and removal
- Implements concurrency control with Promise-based waiting
- Manages player state and card control

**Commands Layer (`src/commands.ts`):**
- Thin glue functions (≤3 lines each)
- Connects HTTP endpoints to Board operations
- Functions: `look()`, `flip()`, `map()`, `watch()`

**HTTP Server (`src/server.ts`):**
- Express-based REST API
- Endpoints: `/look/:id`, `/flip/:id/:row,:col`, `/replace/:id/:from/:to`, `/watch/:id`
- Serves static game UI from `public/` directory
- Port and board file configurable via command line

**Web Interface (`public/index.html`):**
- Bootstrap-styled game interface
- Interactive card grid with click-to-flip
- Real-time updates via polling or long-polling (watch mode)
- Card replacement functionality

---

## Part 2: Game Rules and Mechanics

Memory Scramble implements a comprehensive set of rules governing card flipping, player control, matching, and cleanup operations. These rules ensure fair gameplay and consistent state management in a concurrent multiplayer environment.

### 2.1 Complete Rule Set

#### **RULE 1: Flipping the First Card**

**Rule 1-A: Face-Down Card**
- **Condition:** Player flips a face-down card
- **Action:** Card turns face-up
- **Result:** Player gains control of the card
- **Example:** Player flips hidden card → card reveals value, player controls it

**Rule 1-B: Face-Up Uncontrolled Card**
- **Condition:** Player flips a face-up card that no one controls
- **Action:** Card remains face-up
- **Result:** Player gains control of the card
- **Example:** Card from previous player's non-match → current player takes control

**Rule 1-C: Card Controlled by Another Player**
- **Condition:** Player attempts to flip a card controlled by someone else
- **Action:** Player's flip operation enters waiting state (Promise pending)
- **Result:** Player waits until card becomes available, then gains control
- **Example:** Alice controls card → Bob tries to flip it → Bob waits → Alice finishes → Bob gets control

**Rule 1-D: Empty Space**
- **Condition:** Player attempts to flip an empty space (removed matched card)
- **Action:** Operation throws an error
- **Result:** Error: "no card at (row,col)"
- **Example:** Player tries to flip location where matched cards were removed

---

#### **RULE 2: Flipping the Second Card**

**Rule 2-A: Matching Cards**
- **Condition:** Second card has the same value as first card
- **Action:** Both cards remain face-up
- **Result:** Player maintains control of both cards (scored a match!)
- **Example:** First card = 'A', second card = 'A' → both stay face-up, player controls both

**Rule 2-B: Non-Matching Cards**
- **Condition:** Second card has different value from first card
- **Action:** Both cards remain face-up
- **Result:** Player relinquishes control of both cards (no match)
- **Example:** First card = 'A', second card = 'B' → both stay face-up, player controls neither

**Rule 2-C: Card Controlled by Another Player**
- **Condition:** Player tries to flip a card controlled by someone else as second card
- **Action:** Operation throws an error
- **Result:** Player loses control of first card; error: "card is controlled by another player"
- **Example:** Alice controls first card, tries to flip Bob's controlled card → error, Alice loses first card

**Rule 2-D: Empty Space**
- **Condition:** Player attempts to flip an empty space as second card
- **Action:** Operation throws an error
- **Result:** Player loses control of first card; error: "no card at (row,col)"
- **Example:** Alice flips first card, tries empty space as second → error, Alice loses first card

**Rule 2-E: Same Card Twice**
- **Condition:** Player attempts to flip the same card they just flipped
- **Action:** Operation throws an error (implied by board state)
- **Result:** Player loses control of first card; error: "card is controlled by you"
- **Example:** Flip (0,0) then try (0,0) again → error

---

#### **RULE 3: Finishing Previous Play**

Before a player can make a move, any cards from their previous turn must be cleaned up according to these rules:

**Rule 3-A: Matched Cards Removal**
- **Condition:** Player has two matching cards from previous turn
- **Action:** Both matched cards are removed from the board (become empty spaces)
- **Result:** Spaces at those positions become "none" state
- **Example:** Player matched two 'A' cards at (0,0) and (0,2) → both positions now empty
- **Timing:** Happens when player makes their next flip

**Rule 3-B: Non-Matching Cards Turn Down**
- **Condition:** Face-up cards that are NOT currently controlled by any player
- **Action:** All such cards are turned face-down
- **Result:** Cards return to hidden state for other players to flip
- **Example:** Alice's non-match leaves two face-up cards → Bob starts turn → those cards flip face-down
- **Exception:** Cards controlled by other players remain face-up

---

### 2.2 Card States

Throughout the game, each position on the board can be in one of the following states:

| State | Description | Visual Representation |
|-------|-------------|----------------------|
| **none** | Empty space (matched cards removed) | Empty cell |
| **down** | Face-down card (hidden value) | Gray card back |
| **up CARD** | Face-up uncontrolled card | White cell with card value |
| **my CARD** | Face-up card controlled by you | Yellow cell with card value |

### 2.3 Player States

Each player can be in one of these states:

| State | Description | Cards Controlled |
|-------|-------------|------------------|
| **No cards** | Ready to flip first card | 0 |
| **First card** | Flipped one card, needs second | 1 |
| **Two matching** | Found a match, cards will be removed | 2 (matched) |
| **Two non-matching** | Didn't match, cards stay visible | 0 (relinquished control) |
| **Waiting** | Trying to flip controlled card | 0 (waiting for availability) |

### 2.4 Rule Implementation Summary

These rules work together to create a fair, concurrent multiplayer experience:

1. **Card Access Control:** Rules 1-C and 2-C prevent conflicts by using waiting mechanism
2. **Match Detection:** Rule 2-A identifies successful matches
3. **State Cleanup:** Rules 3-A and 3-B maintain board consistency between turns
4. **Error Handling:** Rules 1-D, 2-C, 2-D, and 2-E provide clear error conditions
5. **Concurrency Safety:** All rules designed to work correctly with multiple simultaneous players

---

## Part 3: Concurrency Handling

### 3.1 The Waiting Mechanism

**Scenario:** Multiple players attempt to flip the same card simultaneously

**Implementation:**
```typescript
// In board.ts - simplified concept
if (space.controlledBy && space.controlledBy !== playerId) {
    // Card is controlled by someone else - wait
    await this.waitForCard(row, column, playerId);
}
```

**Result Screenshot:**

![Concurrent Card Access](./img/concurrent_access.png)

**Explanation:** 
When a player tries to flip a card controlled by another player, the operation doesn't fail immediately. Instead, it waits using Promise-based synchronization. When the controlling player completes their move, waiting players are notified and one of them gains control.

---

### 3.2 Race Condition Prevention

**Critical Section:** Board state modifications

**Protection Mechanism:**
- Promise-based waiting with `Promise.withResolvers()`
- Wait queue management per card position
- Atomic state transitions

**Test Configuration:**
- 4 concurrent players
- 100 random moves each
- Random delays (0.1-2ms)

**Command:**
```bash
npm run simulation
```

**Result Screenshot:**

![Simulation Results]Loaded board: 5x5 from boards/ab.txt

Starting fuzz test: 4 players, 100 moves each
Random delays: 0.1ms - 2ms
Total moves: 400


FUZZ TEST COMPLETE
Completed in: 210ms (0.21s)
Total flips attempted: 419
Successful matches: 8
Failed flips (invalid moves): 225
Card not available (controlled): 14

Moves per second: 1995

Final board state:
Board 5x5:
[     ] [     ] [     ] [     ] [     ] 
[     ] [D↓    ] [D↑    ] [     ] [     ] 
[F↓    ] [F↑    ] [G↓    ] [G↑    ] [     ] 
[     ] [     ] [     ] [     ] [     ] 
[K↑    ] [K↓    ] [     ] [     ] [M↑    ] 

TEST: Multiple Players Waiting for Same Card

Scenario: Alice controls (0,0), Bob and Charlie both want it

[Alice] Flipping (0,0)...
[Alice] Now controls (0,0)

[Bob] Trying to flip (0,0) - should WAIT...
[Charlie] Trying to flip (0,0) - should WAIT...

[System] Bob and Charlie are now waiting...

[Alice] Flipping (0,1) - will release (0,0)...
[Alice] Released (0,0), no match
[Bob] Got the card after waiting 11ms!

✓ Test passed: Waiting mechanism works correctly

TEST: Matched Cards Cleanup

Scenario: Alice matches two cards, Bob waits for one

[Alice] Flipping (0,0)...
[Alice] Flipping (0,2)...

[Alice] Board state:
5x5
my A
down
my A
down
down
down
down
down
down
down
down
down
down
down
down
down
down
down
down
down
down
down
down
down
down

[Alice] MATCHED! Controls both cards

[Bob] Trying to flip (0,0) which Alice controls...
[System] Bob is waiting...

[Alice] Making next move - matched cards should be removed
[Bob] Failed as expected: no card at (0,0)

✓ Test passed: Matched cards removed correctly

✓ ALL TESTS PASSED

Concurrency verification complete:
• Hundreds of moves completed in under a second
• 4 concurrent players with random timing (0.1-2ms)
• Various scenarios tested (waiting, matching, conflicts)
• No crashes, deadlocks, or race conditions detected
• Game remains stable under concurrent load

✓ Problem 3 requirements satisfied!

**Observed Result:** All 400 operations complete successfully without deadlocks or state corruption

---

## Part 4: Testing Strategy

### 4.1 Unit Test Coverage

**Comprehensive test suite (`test/board.test.ts`):**

**Test Categories:**
1. **Board Parsing:** Valid/invalid files, dimension checking
2. **Look Operation:** Face-up/down states, controlled cards, empty spaces
3. **Flip - First Card:** Face-down, face-up, controlled, empty space
4. **Flip - Second Card:** Matching, non-matching, error handling
5. **Finishing Previous Play:** Card removal, turning face-down
6. **Concurrency:** Multiple players, waiting chains, interleaving
7. **Map Operation:** Card transformation, pairwise consistency
8. **Watch Operation:** Change notification, multiple watchers

**Running Tests:**
```bash
npm test
```

**Result Screenshot:**

![Test Results](./img/test_results.png)

**Statistics:**
- Total test cases: 50+
- All tests passing ✓
- Code coverage: High (board.ts, commands.ts)

---

### 4.2 Key Test Examples

**Test: Multiple players waiting for same card**

```typescript
// Alice controls (0,0)
await board.flip("alice", 0, 0);

// Bob and Charlie both wait
const bobPromise = board.flip("bob", 0, 0);
const charliePromise = board.flip("charlie", 0, 0);

// Alice releases
await board.flip("alice", 0, 1);

// One of them gets it
await Promise.race([bobPromise, charliePromise]);
```

**Test: Card removal while others are waiting**

```typescript
// Alice matches and removes cards
await board.flip("alice", 0, 0);
await board.flip("alice", 0, 2); // Match!

// Bob waits for one of the matched cards
const bobPromise = board.flip("bob", 0, 0).catch(() => "failed");

// Alice makes next move - removes matched cards
await board.flip("alice", 1, 0);

// Bob's operation fails (card was removed)
assert.strictEqual(await bobPromise, "failed");
```

---

## Part 5: Real-time Updates

### 5.1 Watch Mechanism

**Purpose:** Long-polling for real-time board updates without constant polling

**Implementation:**
```typescript
// Server endpoint
app.get("/watch/:playerId", (request, response) => {
    void board.watchForChange().then(() => {
        response.send(board.look(playerId));
    });
});
```

**Client Usage:**
- **Polling Mode:** Client requests updates every 500ms
- **Watching Mode:** Client waits for server notification of changes

**Result Screenshot:**

![Watch Mode Interface](./img/watch_mode.png)

**Benefit:** Reduced network traffic and more responsive updates

---


## Conclusion

### Key Achievements

This laboratory work successfully demonstrates advanced concurrent programming concepts in a real-world multiplayer game context:

1. **Concurrency Control:**
   - Promise-based waiting mechanism for card access synchronization
   - Prevention of race conditions in shared game state
   - Deadlock-free design with proper error handling

2. **Multiplayer Support:**
   - Multiple simultaneous players without conflicts
   - Fair access to resources through wait queue management
   - Real-time state synchronization across all clients

3. **Web Architecture:**
   - RESTful API design with Express
   - Long-polling for efficient real-time updates
   - Responsive browser-based UI with Bootstrap

4. **Testing Excellence:**
   - Comprehensive unit test suite (50+ tests)
   - Concurrency stress testing with simulation
   - Edge case coverage (waiting chains, card removal, errors)

