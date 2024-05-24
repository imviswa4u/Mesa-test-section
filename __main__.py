#%% Initializing
### Importing libraries
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from itertools import cycle

### Declaring variables
ASU_colors = cycle(['#8C1D40', '#FFC627', '#78BE20', '#00A3E0', '#Ff9F32', '#5C6670'])
folder_path = r"C:\Users\vissu\Dropbox (ASU)\PC\Documents\GitHub\Mesa Test Section Thermocouple Data\Thermocouple\"

cleaned_dfs = []
air_dfs = []

#%% Reading excel files from os
for filename in os.listdir(folder_path):
    if filename.endswith(".CSV"):
        ### Extracting side and location from filename
        side, location = filename.split(".")[0].split("L")
        side = side[1]
        
        ### Reading excel file into dataframe
        file_path = os.path.join(folder_path, filename)
        df = pd.read_csv(file_path, header=None, names=["date", "time", "temp1", "temp2", "temp3", "temp4"])
        df[["temp1", "temp2", "temp3"]] = df[["temp1", "temp2", "temp3"]].apply(pd.to_numeric, errors="coerce")
        
        
        ### Removing rows with negative or -OL values in temp1, temp2, and temp3
        df = df[(df[["temp1", "temp2", "temp3"]] > 0).all(axis=1)]
        df = df[~df[["temp1", "temp2", "temp3"]].isin(["-OL"]).any(axis=1)]
        df.dropna(subset=["temp1", "temp2", "temp3"], inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        ### Removing rows where temp1 <= temp2 or temp2 <= temp3
        df = df[(df["temp1"] > df["temp2"]) & (df["temp2"] > df["temp3"])]
        df.reset_index(drop=True, inplace=True)
        
        ### Checking if temp1, temp2, and temp3 values are within the range of 170 to 60
        df.dropna(subset=["temp1", "temp2", "temp3"], inplace=True)
        df.reset_index(drop=True, inplace=True)
        # out_of_range_rows = df[(df[["temp1", "temp2", "temp3"]] < 60) | (df[["temp1", "temp2", "temp3"]] > 170)]
        # if not out_of_range_rows.empty:
        #     print(f"Rows with out-of-range values in {filename}:")
        #     print(out_of_range_rows)
        
        ### Compressing the dataframe
        depth_temp_df = pd.melt(df, id_vars=["date", "time"], value_vars=["temp1", "temp2", "temp3"],
                                var_name="Depth", value_name="Temperature")
        depth_temp_df["Depth"] = depth_temp_df["Depth"].map({"temp1": "T", "temp2": "M", "temp3": "B"})
        depth_temp_df["Side"] = side
        depth_temp_df["Location"] = location
        depth_temp_df = depth_temp_df[["Side", "Location", "Depth", "date", "time", "Temperature"]]
        cleaned_dfs.append(depth_temp_df)
        
        ### Creating air temperature dataframe
        if pd.to_numeric(df["temp4"], errors="coerce").notnull().any():
            air_df = df[["date", "time", "temp4"]].copy()
            air_df.columns = ["date", "time", "Temperature"]
            air_df["Location"] = location
            air_df = air_df[["Location", "date", "time", "Temperature"]]
            air_dfs.append(air_df)

#%% Concatenating cleaned dataframes into a single dataframe
### In-depth temperature dataframe
depth_temp = pd.concat(cleaned_dfs, ignore_index=True)
grouped_depth_temp = depth_temp.groupby(["Side", "Location", "Depth"])
least_times = grouped_depth_temp["time"].min()
depth_temp["dTime"] = depth_temp.apply(lambda row: pd.to_datetime(row["time"]) - pd.to_datetime(least_times[row["Side"],
                                                                                                            row["Location"],
                                                                                                            row["Depth"]]), axis=1)
depth_temp["dTime"] = depth_temp["dTime"].dt.total_seconds()
depth_temp.drop("date", axis=1, inplace=True)

### Air temperature dataframe
if air_dfs:
    air_df = pd.concat(air_dfs, ignore_index=True)
else:
    air_df = pd.DataFrame(columns=["Location", "date", "time", "Temperature"])
if "date" in air_df.columns:
    air_df.drop("date", axis=1, inplace=True)


# Print the resulting dataframes
# print("depth_temp dataframe:")
# print(depth_temp)
# print("\nair_df dataframe:")
# print(air_df)

#%% Plotting Data

sns.set(style="whitegrid", context="paper", font_scale=1.2)

### Plot 1: Box plot of temperature distribution for each depth (T, M, B)
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
for i, side in enumerate(["1", "2"]):
    # Filter the data for the current side
    side_data = depth_temp[depth_temp["Side"] == side]
    
    # Create the box plot for the current side
    sns.boxplot(data=side_data, x="Depth", y="Temperature", ax=axes[i])
    
    # Set the title and labels for the current subplot
    axes[i].set_title(f"Temperature Distribution for Different Depths (Side {side})")
    axes[i].set_xlabel("Depth")
    axes[i].set_ylabel("Temperature")

plt.tight_layout()
plt.show();


### Plot 2: Box plot of temperature distribution for each location
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
for i, side in enumerate(["1", "2"]):
    # Filter the data for the current side
    side_data = depth_temp[depth_temp["Side"] == side]
    
    # Create the box plot for the current side
    sns.boxplot(data=side_data, x="Location", y="Temperature", ax=axes[i])
    
    # Set the title and labels for the current subplot
    axes[i].set_title(f"Temperature Distribution for Different Locations (Side {side})")
    axes[i].set_xlabel("Location")
    axes[i].set_ylabel("Temperature")

plt.tight_layout()
plt.show();


### Plot 3: Line plot of temperature over time for each depth (T, M, B) at each location and each side
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# Loop over the sides
for i, side in enumerate(["1", "2"]):
    side_data = depth_temp[depth_temp["Side"] == side]
    used_colors = []

    for location in ["1", "2", "3"]:
        data = side_data[side_data["Location"] == location]
        color = next(ASU_colors)
        used_colors.append(color)
        sns.lineplot(data=data, x="dTime", y="Temperature", style="Depth", label=f"Location: {location}", ax=axes[i], color=color)

    axes[i].set_title(f"Temperature vs. Time for Different Depths and Locations (Side {side})")
    axes[i].set_xlabel("Time (seconds)")
    axes[i].set_ylabel("Temperature")

    handles, labels = axes[i].get_legend_handles_labels()
    depth_handles = handles[:3]
    depth_labels = ["Top", "Middle", "Bottom"]
    
    location_handles = []
    location_labels = []
    for location, color in zip(["1", "2", "3"], used_colors):
        handle = plt.Line2D([], [], color=color, label=f"Location: {location}")
        location_handles.append(handle)
        location_labels.append(f"Location: {location}")
    
    first_legend = axes[i].legend(handles=depth_handles, labels=depth_labels, title="Depth",
                                  loc="upper left", bbox_to_anchor=(1.02, 1))
    axes[i].add_artist(first_legend)
    second_legend = axes[i].legend(handles=location_handles, labels=location_labels, title="Location",
                                   loc="upper left", bbox_to_anchor=(1.02, 0.6))

plt.tight_layout()
plt.show();

