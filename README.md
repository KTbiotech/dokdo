# dokdo

This repository is a collection of Python and R scripts for microbiome sequencing analysis. For details, please see the Wiki page. Pull requests are welcome.

# Simple Example
```
# There is no installation.
import sys
sys.path.append("/path/to/dokdo")
import jejudo

# Create a Jejudo object.
jjd = jejudo.Jejudo()

# Load data.
jjd.read_files("set1/asv.csv", "set1/taxa.csv", "set1/manifest.txt")
```

Describe the Jejudo object using ```jjd.describe()```, which will give:
```
asv_table: [ 1676 taxa and 60 samples ]
tax_table: [ 1676 taxa and 7 ranks ]
smp_table: [ 60 samples and 2 features ]
seq_table: [ 1676 sequences ]
```

```
# Filter out ASVs containing only one non-zero event. 
jjd = jejudo.remove(jjd, n_samples=1)

# Apply log transformation.
jjd = jejudo.transform(jjd, 'l')
```

```
# Plot 2D PCA.
ud = jejudo.ordinate(jjd, 'PCA')
jejudo.plot_ordination(jjd, ud, color='Site', figsize=(15,15), s=100)
plt.savefig('2dpca.png')
```

![2dpca](https://drive.google.com/uc?export=view&id=161zXhaaNeZzRLsAOVy5nBd06hPkaATFT)

```
# Plot 3D PCA.
ud = jejudo.ordinate(jjd, 'PCA', n_components=3)
jejudo.plot_ordination(jjd, ud, color='Site', figsize=(15,15), s=100)
plt.savefig('3dpca.png')
```

![3dpca](https://drive.google.com/uc?export=view&id=19OLG6QC2lE-2WwpGhad2oMZm6CIiY0dO)
