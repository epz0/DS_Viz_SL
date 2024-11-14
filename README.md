# DS-Viz: a method for creating Design Space Visualisations
Pipeline for usign the DS-Viz method to analyse data from the "[effects of creative performance feedback on design outcomes](https://osf.io/zavxc)" experiment. 

## Running the code
  1. Create the Python environment.
  2. Install gower package via pip ($ pip install gower).
  3. Download the dataset from Apollo. (todo)
  4. Run the "test_run.py", "stats_run.py" script for the generation of the DSs, metrics and stats.

## Notes
Code and environment developed on Windows 10. Linux environment created on Ubuntu (todo)

Replicability issues cross platform may occur due to RNG dependencies from UMAP, which is a [known issue](https://github.com/lmcinnes/umap/issues/153). For this  dataset the average difference between participants' DS areas for the full session on Windows vs. Linux was 2.7%.
