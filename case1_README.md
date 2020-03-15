# EF Market Making Files

These files are the ones exclusively used in the market making case

### Files

case1/2019.csv : Historical data used in the test case

case1/BasicMM.py : python file that contains a basic structure for market making using _linear fading_. Important parameters are **width** and **Long Term Fairs** (also called theoretical fairs). 

case1/DATA.zip : Historical data to be used for statistical analysis

example_bot_case1.py : A sample bot that interacts with the exchange.  Uses BasicMM.py

case1/mm_manager.pyc : This runs the market making case, simulating the hedge fund and liquidity bots. You do NOT need to read this file and understanding it will give you little edge in the case.  We recommend instead learning about the liquidity and hedge fund bots from interacting with them in the market.

configs/mm_config.yaml: This controls the parameters of the case.  All the parameters are set as they will be in the case except for "num_competitors".  Currently, it is set for providing the amount of liquidity for one competitor.  On the day of the competition, it will be set to the number of competing teams.  You should change this if you want to test more bots. 


### Other Information

We will separately provide information of xChange and how to run it.  
If you have any questions about these files, please ask questions in the Piazza Case 1 folder.  

