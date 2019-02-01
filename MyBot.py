#!/usr/bin/env python3

# Python 3.6

# ***Map/halite array/list generation and map iteration taken from sentex's halite tutorial.***



# Import the Halite SDK, which will let you interact with the game.

import hlt



# This library contains constant values.

from hlt import constants



# This library contains direction metadata to better interface with the game.

from hlt.positionals import Direction



# This library allows you to generate random numbers.

import random



# Logging allows you to save messages for yourself. This is required because the regular STDOUT
#   (print statements) are reserved for the engine-bot communication.

import logging



""" <<<Game Begin>>> """



# This game object contains the initial game state.

game = hlt.Game()

# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.

game.ready("MyPythonBot")



# Now that your bot is initialized, save a message to yourself in the log file with some important information.
# Here, you log here your id, which you can always fetch from the game object by using my_id.

logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))



""" <<<Game Loop>>> """

# Holds the state of each ship, whether it is in collecting or depositing mode.

ship_states = {}

while True:
    
# This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
#   running update_frame().
    
    game.update_frame()
    
# You extract player metadata and the updated map metadata here for convenience.
    
    me = game.me
    
    game_map = game.game_map
    
    
    
# A command queue holds all the commands you will run this turn. You build this list up and submit it at the
#   end of the turn.
    
    
    command_queue = []
    
# The directions of which each ship can move, including staying still.
    
    direction_order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]
    
# The choice position each ship makes.
    
    position_choices = []
    
# Iterating through the list of ships, if the ship does not have a state it is
# assigned the collecting state. 
    
    for ship in me.get_ships():
        
        if ship.id not in ship_states:
            
            ship_states[ship.id] = "collecting"
    
        
        position_options = ship.position.get_surrounding_cardinals() + [ship.position]
        
# Contains movement mapped to a coordinate.
        
        position_dict = {}
        
# Contains the actual movement based on the halite.
        
        halite_dict = {}
        
        
# Maps and fills the position dictionary.
        
        for n, direction in enumerate(direction_order):
            
            position_dict[direction] = position_options[n]
        
        
# Maps and fills the halite dictionary. Finds the halite amount of the positions.
# If statement for if the ship has the direction still, which changes
# the halite_amount to halite_amount*2. This fixes the ships not staying still
# long enough to collect all the halite of a position.
            
            
        for direction in position_dict:
            
            position = position_dict[direction]
            
            halite_amount = game_map[position].halite_amount
            
            if position_dict[direction] not in position_choices:
                
                if direction == Direction.Still:
                    
                    halite_dict[direction] = halite_amount*2
            
                else:
                    
                    halite_dict[direction] = halite_amount
        else:
            logging.info("moving to same spot\n")
        


# If statement condition for if a ship is depositing. The ship calculates
# the distance of the shipyard and dropoff (if a dropoff is spawned)
# and calculates which shipyard/dropoff is closest based on total distance.
# this then determines which station to naive_navigate to.
# An if statement at the bottom to not populate the command queue if the
# turn is 250, so that only one command is in the queue for that turn.
# (drop off spawn at 250)
        
        if ship_states[ship.id] == "depositing":
            
            
            distance = game_map.calculate_distance(ship.position, me.shipyard.position)
            logging.info("shipyard distance:")
            logging.info(distance)
            
            if len(me.get_dropoffs()) != 0:
                dropoffs = me.get_dropoffs()
                pos = dropoffs[0].position
                logging.info("dropoff distance:")
                distance2 = game_map.calculate_distance(ship.position,pos)
                logging.info(distance2)
                if distance > distance2:
                    move = game_map.naive_navigate(ship, pos)
                else:
                    move = game_map.naive_navigate(ship, me.shipyard.position)
            else:
                move = game_map.naive_navigate(ship, me.shipyard.position)
  
            
            position_choices.append(position_dict[move])

            
            if game.turn_number != 250:
            
                command_queue.append(ship.move(move))
                
            
            if move == Direction.Still:
                ship_states[ship.id] = "collecting"


#Collecting else if statement. Creates a directional choice based on the
# amount of halite on the surrounding positions.
# The best option (max) gets stored and created as a positional choice
# to then be put into the commmand_queue if the turn isn't 250 (drop off spawn turn).

        elif ship_states[ship.id] == "collecting":

            
            directional_choice = max(halite_dict, key=halite_dict.get)
            
            position_choices.append(position_dict[directional_choice])
            
            halite_of_position = game_map[ship.position].halite_amount
            
            if game.turn_number != 250 and ship.halite_amount >= halite_of_position * .10:
            
                command_queue.append(ship.move(game_map.naive_navigate(ship,position_dict[directional_choice])))
            
            
            
#Based on the round, change the ship halite amount of when the ship
# returns back to the depositing state.
            
            if game.turn_number <= 200 and ship.halite_amount > constants.MAX_HALITE * 0.95:
                
                ship_states[ship.id] = "depositing"
                
            if game.turn_number > 200 and game.turn_number <= 350 and ship.halite_amount > constants.MAX_HALITE * 0.90:
                
                ship_states[ship.id] = "depositing"
                
            if game.turn_number > 350 and ship.halite_amount > constants.MAX_HALITE * 0.80:
                
                ship_states[ship.id] = "depositing"    
    


# If the game is in the first 200 turns and you have enough halite, spawn a ship.
# Don't spawn a ship if you currently have a ship at port, though - the ships will collide.         
# hard cap on the amount of ships spawned at 25. Another if statement if the turn is exactly
# 250, then spawn a dropoff.                

    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
    
        command_queue.append(me.shipyard.spawn())
        
    if game.turn_number == 250 and me.halite_amount >= constants.DROPOFF_COST and not game_map[ship.position] == game_map[me.shipyard.position]:
    
        command_queue.append(ship.make_dropoff())
    
    
    
# Send your moves back to the game environment, ending this turn.
    
    game.end_turn(command_queue)