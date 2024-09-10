var TOTAL_TURNS = 10
var MAX_EXPECTED_CALCULATIONS = 131128140
var possibilities_calculated = 0
var wins_calculated = 0
var orders_calculated = 0
var winning_orders_calculated = 0
var top_winning_states = []
var top_winning_state_areas = []
var TOP_WINNING_STATES_MAX_COUNT = 100
var EDGE_TILES_SET = new Set([0, 1, 2, 3, 4, 5, 6, 7, 14, 21, 28, 35, 13, 20, 27, 34, 41, 42, 43, 44, 45, 46, 47, 48])
var EDGE_TILE_MIMIC_PRIORITY_MAP = {42:0,43:1,44:2,45:3,46:4,47:5,48:6,35:7,41:8,28:9,34:10,21:11,27:12,14:13,20:14,7:15,13:16,0:17,1:18,2:19,3:20,4:21,5:22,6:23}
var MIMIC_MOVEMENT_DIRECTION_CHAINS = []
var MIMIC_MOVEMENT_UP_TILES = []
var MIMIC_MOVEMENT_UP_LEFT_TILES = []
var MIMIC_MOVEMENT_UP_RIGHT_TILES = []
var MIMIC_MOVEMENT_DOWN_TILES = []
var MIMIC_MOVEMENT_DOWN_LEFT_TILES = []
var MIMIC_MOVEMENT_DOWN_RIGHT_TILES = []
var exit_found = false

//seed these two to their max capacity to simplify logic later
for (var i=0; i<TOP_WINNING_STATES_MAX_COUNT; i++) {
    top_winning_states.push(-1)
    top_winning_state_areas.push(-1)
}

var GRID = []
//top row has 0-6, second row 7-13, etc until final row which should have 42-48
for(var i=0; i<49; i++) {
    GRID[i] = new Set()
    hex_is_lowered = i % 7 == 1 || i % 7 == 3 || i % 7 == 5
    hex_is_raised = !hex_is_lowered

    // up: only if we're below the top row
    if (i > 6) {
        GRID[i].add(i - 7)
        MIMIC_MOVEMENT_UP_TILES[i] = i - 7
    }
    // down: only if we're above the bottom row
    if (i < 42) {
        GRID[i].add(i + 7)
        MIMIC_MOVEMENT_DOWN_TILES[i] = i + 7
    }
    // left: only if we're outside the left column
    if (i % 7 > 0)
        GRID[i].add(i - 1)
    // right: only if we're outside the right column
    if (i % 7 < 6)
        GRID[i].add(i + 1)
    // down-left: we need to satisfy both down and left criteria, and be a "lowered" hex
    if ((i < 42) && (i % 7 > 0) && hex_is_lowered)
        GRID[i].add(i + 7 - 1)
    // down-right: we need to satisfy both down and right criteria, and be a "lowered" hex
    if ((i < 42) && (i % 7 < 6) && hex_is_lowered)
        GRID[i].add(i + 7 + 1)
    // up-left: satisfy both up and left criteria, and be a "raised" hex
    if ((i > 6) && (i % 7 > 0) && hex_is_raised)
        GRID[i].add(i - 7 - 1)
    // up-right: satisfy both up and right criteria, and be a "raised" hex
    if ((i > 6) && (i % 7 < 6) && hex_is_raised)
        GRID[i].add(i - 7 + 1)

    // for MIMIC MOVEMENT ARRAYS
    // after first row, and not in the rightmost column
    if (i > 6 && i % 7 < 6) {
        if (hex_is_raised)
            MIMIC_MOVEMENT_UP_RIGHT_TILES[i] = i - 6
    }
    // not in right column
    if (i % 7 < 6) {
        if (hex_is_lowered)
            MIMIC_MOVEMENT_UP_RIGHT_TILES[i] = i + 1
    }
    // after first row, and not in the leftmost column
    if (i > 6 && i % 7 > 0) {
        if (hex_is_raised)
            MIMIC_MOVEMENT_UP_LEFT_TILES[i] = i - 8
    }
    // not in the leftmost column
    if (i % 7 > 0) {
        if (hex_is_lowered)
            MIMIC_MOVEMENT_UP_LEFT_TILES[i] = i - 1
    }
    // not in the leftmost column
    if (i % 7 > 0) {
        if (hex_is_raised)
            MIMIC_MOVEMENT_DOWN_LEFT_TILES[i] = i - 1
    }
    // before last row, and not in the leftmost column
    if (i < 42 && i % 7 > 0) {
        if (hex_is_lowered)
            MIMIC_MOVEMENT_DOWN_LEFT_TILES[i] = i + 6
    }
    // not in the rightmost column
    if (i % 7 < 6) {
        if (hex_is_raised)
            MIMIC_MOVEMENT_DOWN_RIGHT_TILES[i] = i + 1
    }
    // before last row, and not in the rightmost column
    if (i < 42 && i % 7 < 6) {
        if (hex_is_lowered)
            MIMIC_MOVEMENT_DOWN_RIGHT_TILES[i] = i + 8
    }
}

for(var i=0; i<49; i++) {
    // the mimic prefers to take the left-most route, so we will build chains that connect an adjacent tile to the next counter-clockwise one, for every tile (except for the up special case)
    MIMIC_MOVEMENT_DIRECTION_CHAINS[i] = {}

    // up-right -> up
    if (MIMIC_MOVEMENT_UP_RIGHT_TILES[i] !== undefined && MIMIC_MOVEMENT_UP_TILES[i] !== undefined) {
        MIMIC_MOVEMENT_DIRECTION_CHAINS[i][MIMIC_MOVEMENT_UP_RIGHT_TILES[i]] = MIMIC_MOVEMENT_UP_TILES[i]
    }
    // NOTE: THIS IS A SPECIAL CASE BASED ON OBSERVATIONS OF THE MIMIC INGAME. NOT A MISTAKE
    // up-left -> up
    if (MIMIC_MOVEMENT_UP_LEFT_TILES[i] !== undefined && MIMIC_MOVEMENT_UP_TILES[i] !== undefined) {
        MIMIC_MOVEMENT_DIRECTION_CHAINS[i][MIMIC_MOVEMENT_UP_LEFT_TILES[i]] = MIMIC_MOVEMENT_UP_TILES[i]
    }
    // up-left -> down-left
    if (MIMIC_MOVEMENT_UP_LEFT_TILES[i] !== undefined && MIMIC_MOVEMENT_DOWN_LEFT_TILES[i] !== undefined) {
        MIMIC_MOVEMENT_DIRECTION_CHAINS[i][MIMIC_MOVEMENT_UP_LEFT_TILES[i]] = MIMIC_MOVEMENT_DOWN_LEFT_TILES[i]
    }
    // down-left -> down
    if (MIMIC_MOVEMENT_DOWN_LEFT_TILES[i] !== undefined && MIMIC_MOVEMENT_DOWN_TILES[i] !== undefined) {
        MIMIC_MOVEMENT_DIRECTION_CHAINS[i][MIMIC_MOVEMENT_DOWN_LEFT_TILES[i]] = MIMIC_MOVEMENT_DOWN_TILES[i]
    }
    // down -> down-right
    if (MIMIC_MOVEMENT_DOWN_TILES[i] !== undefined && MIMIC_MOVEMENT_DOWN_RIGHT_TILES[i] !== undefined) {
        MIMIC_MOVEMENT_DIRECTION_CHAINS[i][MIMIC_MOVEMENT_DOWN_TILES[i]] = MIMIC_MOVEMENT_DOWN_RIGHT_TILES[i]
    }
    // down-right -> up-right
    if (MIMIC_MOVEMENT_DOWN_RIGHT_TILES[i] !== undefined && MIMIC_MOVEMENT_UP_RIGHT_TILES[i] !== undefined) {
        MIMIC_MOVEMENT_DIRECTION_CHAINS[i][MIMIC_MOVEMENT_DOWN_RIGHT_TILES[i]] = MIMIC_MOVEMENT_UP_RIGHT_TILES[i]
    }
}

// state is an array which for every tile, says true if it's green / passable, and false if it's void / bombed / impassable
function captureBoardState() {
    var out = [];
    // Select all elements with class 'hexagon' that are descendants of elements with class 'tile' inside the element with id 'board'
    var hexagons = document.querySelectorAll('#board > .tile > .hexagon');
    
    hexagons.forEach(function(hexagon) {
        // Check if the element does not have the 'void' class
        out.push(!hexagon.classList.contains('void'));
    });

    return out;
}


function dfsLookForExit(state, tile, seen) {
    if (EDGE_TILES_SET.has(tile)) {
        exit_found = true
        return true
    }
    seen[tile] = true
    GRID[tile].forEach(function(neighbor) {
        if (exit_found) {
            return
        }
        if(state[neighbor] && !seen[neighbor]) {
            dfsLookForExit(state, neighbor, seen)
        }
    })
}

function isWinningState(state) {
    //since DFS on all possibilities is too slow, let's try to improve performance by quickly identifying all 3-step escape paths
    // straight down to 38 exits
    if (state[31] && state[38] && (state[44] || state[45] || state[46])) {
        return false
    }
    //down to 44
    if (state[30] && state[37] && state[44]) {
        return false
    }
    //down to 46
    if (state[32] && state[39] && state[46]) {
        return false
    }
    // straight up to 3
    if (state[17] && state[10] && state[3]) {
        return false
    }
    // left to 15 exits
    if (state[23] && state[15] && (state[14] || state[21])) {
        return false
    }
    // left to 22 exits
    if ((state[23] || state[30]) && state[22] && (state[21] || state[28])) {
        return false
    }
    // left to 29 exits
    if (state[30] && state[29] && (state[28] || state[35])) {
        return false
    }
    // right to 19 exits
    if (state[25] && state[19] && (state[20] || state[27])) {
        return false
    }
    // right to 26 exits
    if ((state[25] || state[32]) && state[26] && (state[27] || state[34])) {
        return false
    }
    // right to 33 exits
    if (state[32] && state[33] && (state[34] || state[41])) {
        return false
    }

    seen = []
    // the index of the center piece should be 24, so that's where we will begin our DFS
    exit_found = false
    dfsLookForExit(state, 24, seen)
    if (exit_found) {
        return false
    }
    // at this point, we have a viable strategy, and the seen list should tell us the area, so we can store that info
    seen_count = seen.filter(bool => bool === true).length;
    if (seen_count > top_winning_state_areas[top_winning_state_areas.length - 1]) {
        //find the position in the top-10 list where this should belong
        for (var i=0; i<top_winning_state_areas.length; i++) {
            if (seen_count >= top_winning_state_areas[i]) {
                top_winning_states.splice(i, 0, Array.from(state))
                top_winning_state_areas.splice(i, 0, seen_count)
                top_winning_states.pop()
                top_winning_state_areas.pop()
                break
            }
        }
    }
    return true
}



// recursion to iterate through the board and place bombs can be similar logic to bingo board
function calculatePossibilitiesForState(state, tile, turns_used) {
    if(turns_used >= TOTAL_TURNS) {
        possibilities_calculated++;
        if (possibilities_calculated % 1000000 == 0) {
            let percentage = possibilities_calculated / MAX_EXPECTED_CALCULATIONS;
            percentage = `${Math.floor(percentage * 100)}%`;
            
            // Update the progress bar's CSS custom property
            let progressBar = $("#solve_progressbar_blue");
            progressBar.width(percentage);
            progressBar.text(percentage);
        }
        if(isWinningState(state)) {
            wins_calculated++;
        }
        return;
    }
    if(tile >= 49) {
        return;
    }

    // We want to skip the middle tile and not even consider it as a bombing target.
    // I could theoretically imagine strategies where it could be bombed, but they don't seem optimal anyways.
    if(state[tile] == false || tile == 24 || tile == 0 || tile == 6) {
        if (possibilities_calculated % 100000 == 0) {
            // need to use setTimeout to allow the UI to update, otherwise it gets fully blocked until all 131m are done
            setTimeout(calculatePossibilitiesForState, 0, Array.from(state), tile+1, turns_used)
        } else {
            calculatePossibilitiesForState(state, tile+1, turns_used);
        }
    } else {
        state[tile] = false;
        calculatePossibilitiesForState(state, tile+1, turns_used+1);
        state[tile] = true;
        calculatePossibilitiesForState(state, tile+1, turns_used);
    }
}

document.querySelectorAll('#board .tile .hexagon').forEach(hexagon => {
    hexagon.addEventListener('click', function () {
        this.classList.toggle("void");
        handleTileClick();
    });
});


var setup_turns_remaining = 0

function handleTileClick() {
    // Get the number of tiles with class 'void' under '#board .hexagon'
    const voidCount = document.querySelectorAll('#board .hexagon.void').length;
    const setup_turns_remaining = 14 - voidCount;

    // Update the text content of the slot element
    const slotElement = document.querySelector("#void-turns > .slot");
    if (slotElement) {
        slotElement.textContent = setup_turns_remaining;
    }
}

function bfsGetDistanceToTargetTile(state, current, target) {
    queue = []
    queue_index = 0
    seen = []
    depth = 0
    queue.push(current)
    queue.push(-1)

    while(queue_index < queue.length) {
        tile = queue[queue_index]
        queue_index += 1
        if( tile == -1 ) {
            depth += 1
            if( queue_index < queue.length ) {
                queue.push(-1)
            }
            continue
        }
        if( tile == target ) {
            return depth
        }
        seen[tile] = true
        GRID[tile].forEach(function(neighbor) {
            if(state[neighbor] && !seen[neighbor]) {
                queue.push(neighbor)
            }
        })
    }
}

function calculateShortestOpenPathFromCenterToTile(state, tile) {
    return bfsGetDistanceToTargetTile(state, 24, tile)
}

function simulateMimicMove(state, mimic) {
    mimic = Number(mimic)
    // this is basically gonna be BFS, but if we find an edge, we'll keep going until we reach the next divisor, then pick among the found escape paths if there are multiple
    queue = []
    queue_index = 0
    seen = []
    GRID[mimic].forEach(function(neighbor) {
        if(state[neighbor]) {
            queue.push([neighbor, neighbor])
        }
        seen[neighbor] = true
    })
    queue.push([-1, -1])

    // escape_paths will now be an array of tuples, holding the adjacent mimic tile for that path, and the edge tile the path leads to
    escape_paths = []

    while(queue_index < queue.length) {
        tile_tuple = queue[queue_index]
        tile = tile_tuple[1]
        queue_index += 1
        if( tile == -1 ) {
            if(escape_paths.length > 0) {
                //reaching a depth divisor is reason to stop, if we have found an escape path
                break
            }
            if( queue_index < queue.length) {
                queue.push([-1, -1])
            }
            continue
        }
        if( EDGE_TILES_SET.has(tile)) {
            escape_paths.push([tile_tuple[0], tile])
        }
        seen[tile] = true
        GRID[tile].forEach(function(neighbor) {
            if(state[neighbor] && !seen[neighbor]) {
                queue.push([tile_tuple[0], neighbor])
            }
        })
    }
    if (escape_paths.length == 0) {
        return mimic
    }
    escape_paths.sort(function(a, b) {
        return EDGE_TILE_MIMIC_PRIORITY_MAP[a[1]] - EDGE_TILE_MIMIC_PRIORITY_MAP[b[1]]
    })

    //if all escape paths share the same adjacent tile, just take that step immediately
    escape_set = new Set(escape_paths.map(path => path[0]))
    if (escape_set.size == 1) {
        return escape_paths[0][0]
    }

    // we want to collect all escape paths with the same target edge tile as the highest priority escape path
    mimics_favorite_escape_paths = []
    mimics_favorite_escape_paths.push(escape_paths[0])
    for (var i=1; i < escape_paths.length; i++) {
        if (escape_paths[i][1] == mimics_favorite_escape_paths[0][1]) {
            mimics_favorite_escape_paths.push(escape_paths[i])
        }
    }

    // if all of the mimic's favorite escape paths share the same adjacent tile, take that step immediately
    favorite_escape_moves_set = new Set(mimics_favorite_escape_paths.map(path => path[0]))
    if (favorite_escape_moves_set.size == 1) {
        return mimics_favorite_escape_paths[0][0]
    }

    // otherwise, we apply some sophisticated logic to decide which path towards the target the mimic will prefer
    // specifically, we tie-break on the "left-most" or counter-clockwise option according to the mimic's perspective
    favorite_escape_moves = Array.from(favorite_escape_moves_set)
    var first_move_next = MIMIC_MOVEMENT_DIRECTION_CHAINS[mimic][favorite_escape_moves[0]]
    // first we check for a very rare situation where we are forked upwards. this is a bizarre special case but we need to tie-break to the right if it happens
    if (favorite_escape_moves_set.has(MIMIC_MOVEMENT_UP_LEFT_TILES[mimic]) && favorite_escape_moves_set.has(MIMIC_MOVEMENT_UP_RIGHT_TILES[mimic]) && !favorite_escape_moves_set.has(MIMIC_MOVEMENT_UP_TILES[mimic])) {
        return MIMIC_MOVEMENT_UP_RIGHT_TILES[mimic]
    }
    // next we check for a fairly rare situation where a void tile forks the two options we need to tie-break
    else if(favorite_escape_moves_set.has(MIMIC_MOVEMENT_DIRECTION_CHAINS[mimic][first_move_next])) {
        return MIMIC_MOVEMENT_DIRECTION_CHAINS[mimic][first_move_next]
    }
    // here we check for the most likely tie-break where the two options are next to each-other. we pick according to the direction chains logic, which has a special case for up vs up-left
    else if(favorite_escape_moves_set.has(first_move_next)) {
        return first_move_next
    } else {
        return favorite_escape_moves[0]
    }
    return mimic
}

function calculateBombingOrder(state, chosen_bombing_targets) {
    console.log("state passed into calculateBombingOrder:", state)
    console.log("chosen_bombing_targets passed into calculateBombingOrder:", chosen_bombing_targets)
    chosen_bombing_targets.reverse()
    console.log("chosen_bombing_targets after reversal pass:", chosen_bombing_targets)
    chosen_bombing_targets_proximity = []
    for( var i = 0; i < 10; i++) {
        chosen_bombing_targets_proximity[i] = calculateShortestOpenPathFromCenterToTile(state, chosen_bombing_targets[i])
    }
    console.log("calculated proximity of each bombing target as follows:", chosen_bombing_targets_proximity)

    var combined = chosen_bombing_targets.map((item, index) => {
      return { value: item, sortBy: chosen_bombing_targets_proximity[index] };
    });
    combined.sort((a, b) => a.sortBy - b.sortBy);
    var chosen_bombing_targets_in_proximity_order = combined.map(item => item.value);
    console.log("ordered bombing targets by proximity:", chosen_bombing_targets_in_proximity_order)

    // now we want to iterate through permutations of bombing order
    var best_bombing_order = Array.from(chosen_bombing_targets_in_proximity_order)
    var best_mimic_movement_stack = []
    var best_bombing_order_area = 0
    var candidate_order = [0]
    state[chosen_bombing_targets[0]] = false
    var mimic_movement_stack = [24]
    var should_force_increment = false
    mimic_movement_stack.push(simulateMimicMove(state, 24))
    while (candidate_order[0] < 10) {
        orders_calculated += 1
        //check if mimic is at the edge
        if (should_force_increment == true || EDGE_TILES_SET.has(mimic_movement_stack[mimic_movement_stack.length - 1])) {
            should_force_increment = false
            // if so, then we want to rollback his movement and change the last number in the candidate order
            mimic_movement_stack.pop()
            var incremented = false
            while (incremented == false) {
                while (candidate_order[candidate_order.length - 1] >= 9) {
                    // if the last number in the candidate order is already a 9, then we rollback another movement and increment the previous
                    mimic_movement_stack.pop()
                    state[chosen_bombing_targets[candidate_order.pop()]] = true
                }
                state[chosen_bombing_targets[candidate_order[candidate_order.length - 1]]] = true
                candidate_order_set = new Set(candidate_order)
                for (var i=candidate_order[candidate_order.length - 1] + 1; i<10; i++) {
                    if(!candidate_order_set.has(i)) {
                        candidate_order[candidate_order.length - 1] = i
                        incremented = true
                        break
                    }
                }
                // it can happen that we try to increment 8 to 9, but 9 is already present earlier in the array, so in this case we should pop
                if (!incremented) {
                    mimic_movement_stack.pop()
                    state[chosen_bombing_targets[candidate_order.pop()]] = true
                    //detect case where the bombing strategy is non-viable
                    if (candidate_order.length == 1 && candidate_order[0] == 9) {
                        candidate_order[0] = 10
                        break
                    }
                }
            }

            state[chosen_bombing_targets[candidate_order[candidate_order.length - 1]]] = false
        } else {
            // however, if the mimic is not at an edge,
            // then we want to see if we have already successfully bombed ten tiles. if so, see how many tiles the mimic walked on, and save it if it has more than the current best
            if (candidate_order.length == 10) {
                // even if we bombed 10 tiles and mimic didn't reach an edge, he could still be outside the capture zone. so we need to DFS for the edge
                exit_found = false
                dfsLookForExit(state, mimic_movement_stack[mimic_movement_stack.length - 1], [])
                if(exit_found) {
                    // non-viable bombing order, need to force an increment
                    should_force_increment = true
                    continue
                }

                winning_orders_calculated += 1
                bombing_order_out = []
                for (var i=0; i<10; i++) {
                    bombing_order_out[i] = chosen_bombing_targets[candidate_order[i]]
                }
                mimic_movement_set = new Set(mimic_movement_stack)
                if (mimic_movement_set.size > best_bombing_order_area) {
                    best_bombing_order_area = mimic_movement_set.size
                    best_bombing_order = Array.from(bombing_order_out)
                    best_mimic_movement_stack = Array.from(mimic_movement_stack)
                }
                should_force_increment = true
                continue
            }
            // otherwise, we add another number to the order and simulate the mimic's movement
            candidate_order_set = new Set(candidate_order)
            for (var i=0; i<10; i++) {
                if(!candidate_order_set.has(i)) {
                    candidate_order.push(i)
                    state[chosen_bombing_targets[i]] = false
                    break
                }
            }
        }
        //whether we incremented the last number, or added a new one, we need to simulate the mimic's movement appropriately
        mimic_movement_stack.push(simulateMimicMove(state, mimic_movement_stack[mimic_movement_stack.length - 1]))
    }
    return [best_bombing_order,best_mimic_movement_stack]

}

function deriveChosenBombingOrderFromState(original_state, bombed_state) {
    out = []
    for (var i=0; i<bombed_state.length; i++) {
        if (original_state[i] == true && bombed_state[i] == false) {
            out.push(i)
        }
    }
    return out
}

function handleCalculationsCompleted() {
    $("#solve_progressbar_blue").text("100%");
    let chosen_bombing_targets = deriveChosenBombingOrderFromState(captureBoardState(), top_winning_states[0]);
    document.querySelectorAll('#board .tile .hexagon').forEach(hexagon => hexagon.textContent = "");

    let bombing_order_tuple = calculateBombingOrder(captureBoardState(), chosen_bombing_targets);
    let alternative_index = 0;
    
    while (bombing_order_tuple[1].length === 0) {
        if (alternative_index < top_winning_states.length - 1) {
            alternative_index += 1;
        } else {
            break;
        }
        chosen_bombing_targets = deriveChosenBombingOrderFromState(captureBoardState(), top_winning_states[alternative_index]);
        bombing_order_tuple = calculateBombingOrder(captureBoardState(), chosen_bombing_targets);
    }
    paintOrder(bombing_order_tuple[0], top_winning_state_areas[0]);
}

document.querySelector('#calculate').addEventListener("click", function() {
    possibilities_calculated = 0;
    wins_calculated = 0;
    const setupTurnsRemaining = setup_turns_remaining;
    const board_state_for_capture_calcs = captureBoardState();

    let number_of_excluded_tiles = 17; // 17 is the best-case scenario

    if (!board_state_for_capture_calcs[0]) {
        number_of_excluded_tiles -= 1;
    }
    if (!board_state_for_capture_calcs[6]) {
        number_of_excluded_tiles -= 1;
    }
    if (setupTurnsRemaining === 1) {
        number_of_excluded_tiles -= 1;
    }

    switch (number_of_excluded_tiles) {
        case 17:
            MAX_EXPECTED_CALCULATIONS = 64512240;
            break;
        case 16:
            MAX_EXPECTED_CALCULATIONS = 92561040;
            break;
        case 15:
            MAX_EXPECTED_CALCULATIONS = 131128140;
            break;
        case 14:
            MAX_EXPECTED_CALCULATIONS = 183579396;
            break;
    }

    calculatePossibilitiesForState(board_state_for_capture_calcs, 0, 0);

    const calculationWaiter = setInterval(function() {
        if (possibilities_calculated >= MAX_EXPECTED_CALCULATIONS) {
            clearInterval(calculationWaiter);
            handleCalculationsCompleted();
        }
    }, 100);
});


handleTileClick()


const hexagon24 = document.querySelector('#_24 .hexagon');
if (hexagon24) {
    hexagon24.removeEventListener("click", null); // Remove all click event listeners
}

if (hexagon24) {
    hexagon24.classList.add('mimic0');
}
