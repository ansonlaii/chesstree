# chesstree

A visualizer for chess moves in woman grandmaster games to visualize how different moves branch out from the starting positions. Each move is represented by a rectangle where the larger the rectangle the more popular the move. The user can click the rectangle and expand it to see the next popular move and press "o" to open the webpage that links to the actual game in lichess. The moves of WGM games are stored in the json files and one can change the files to visualize different set of chess games. tm_trees contains the classes that define the basic tree interface and treemap_visualizer is the module to run the visualizer. 
