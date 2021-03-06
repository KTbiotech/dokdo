# Import standard libraries.
import math
import tempfile
import warnings
import numbers

# Import external libraries.
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import skbio as sb
from scipy import stats

# Import QIIME 2 libraries
import qiime2
from qiime2 import Artifact
from qiime2 import Metadata
from qiime2 import Visualization
from qiime2.plugins import feature_table
from qiime2.plugins import diversity_lib
from qiime2.plugins import diversity










# -- Private methods ---------------------------------------------------------

def _get_mf_cols(df):
    "Returns metadata columns from DataFrame object."
    cols = []
    for column in df.columns:
        if 'Unassigned' in column:
            continue
        elif '__' in column:
            continue
        else:
            cols.append(column)
    return cols










def _filter_samples(df, mf, exclude_samples, include_samples):
    "Returns DataFrame objects after sample filtering."
    if exclude_samples and include_samples:
        m = ("Cannot use 'exclude_samples' and "
             "'include_samples' arguments together")
        raise ValueError(m)
    elif exclude_samples:
        for x in exclude_samples:
            for y in exclude_samples[x]:
                i = mf[x] != y
                df = df.loc[i]
                mf = mf.loc[i]
    elif include_samples:
        for x in include_samples:
            i = mf[x].isin(include_samples[x])
            df = df.loc[i]
            mf = mf.loc[i]
    else:
        pass
    return (df, mf)










def _sort_by_mean(df):
    "Returns DataFrame object after sorting taxa by mean relative abundance."
    a = df.div(df.sum(axis=1), axis=0)
    a = a.loc[:, a.mean().sort_values(ascending=False).index]
    return df[a.columns]










def _pretty_taxa(s):
    "Returns pretty taxa name."
    if isinstance(s, matplotlib.text.Text):
        s = s.get_text()
    ranks = list(reversed(s.split(';')))

    for i, rank in enumerate(ranks):
        if rank in ['Others', 'Unassigned']:
            return rank

        if rank == '__':
            continue

        if rank.split('__')[1] is '':
            continue

        if 'uncultured' in rank:
            continue

        # The species name can be sometimes tricky to parse because it could 
        # be full (e.g. Helicobacter pylori) or partial (e.g. pylori). In the 
        # latter case, I will borrow the genus name (e.g. Helicobacter) to 
        # form the full species name.
        if 's__' in rank:
            rank = rank.split('__')[1]

            if len(rank.split('_')) == 1:
                genus = ranks[i+1].split('__')[1].split('_')[0]
                species = rank.split('_')[0]
                rank = f'{genus} {species}'
            else:
                rank = rank.replace('_', ' ')

        if '__' in rank:
            rank = rank.split('__')[1]

        return rank










def _artist(ax,
            title=None,
            title_fontsize=None,
            xlabel=None,
            xlabel_fontsize=None,
            ylabel=None,
            ylabel_fontsize=None,
            zlabel=None,
            zlabel_fontsize=None,
            hide_xtexts=False,
            hide_ytexts=False,
            hide_ztexts=False,
            hide_xlabel=False,
            hide_ylabel=False,
            hide_zlabel=False,
            hide_xticks=False,
            hide_yticks=False,
            hide_zticks=False,
            hide_xticklabels=False,
            hide_yticklabels=False,
            hide_zticklabels=False,
            xticks=None,
            yticks=None,
            xticklabels=None,
            xticklabels_fontsize=None,
            yticklabels=None,
            yticklabels_fontsize=None,
            xrot=None,
            xha=None,
            xmin=None,
            xmax=None,
            ymin=None,
            ymax=None,
            xlog=False,
            ylog=False,
            show_legend=False,
            legend_loc='best',
            legend_ncol=1,
            legend_labels=None,
            legend_short=False,
            remove_duplicates=False,
            legend_only=False,
            legend_fontsize=None,
            legend_markerscale=None):
    """
    This method controls various properties of a figure.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes object to draw the plot onto.
    title : str, optional
        Sets the figure title.
    title_fontsize : float or str, optional
        Sets the title font size.
    xlabel : str, optional
        Set the x-axis label.
    xlabel_fontsize : float or str, optional
        Sets the x-axis label font size.
    ylabel : str, optional
        Set the y-axis label.
    ylabel_fontsize : float or str, optional
        Sets the y-axis label font size.
    zlabel : str, optional
        Set the z-axis label.
    zlabel_fontsize : float or str, optional
        Sets the z-axis label font size.
    hide_xtexts : bool, default: False
        Hides all the x-axis texts.
    hide_ytexts : bool, default: False
        Hides all the y-axis texts.
    hide_ztexts : bool, default: False
        Hides all the z-axis texts.
    hide_xlabel : bool, default: False
        Hides the x-axis label.
    hide_ylabel : bool, default: False
        Hides the y-axis label.
    hide_zlabel : bool, default: False
        Hides the z-axis label.
    hide_xticks : bool, default: False
        Hides ticks and tick labels for the x-axis.
    hide_yticks : bool, default: False
        Hides ticks and tick labels for the y-axis.
    hide_zticks : bool, default: False
        Hides ticks and tick labels for the z-axis.
    hide_xticklabels : bool, default: False
        Hides tick labels for the x-axis.
    hide_yticklabels : bool, default: False
        Hides tick labels for the y-axis.
    hide_zticklabels : bool, default: False
        Hides tick labels for the z-axis.
    xticks : list, optional
        Positions of x-axis ticks.
    yticks : list, optional
        Positions of y-axis ticks.
    xticklabels : list, optional
        Tick labels for the x-axis.
    xticklabels_fontsize : float or str, optional
        Font size for the x-axis tick labels.
    yticklabels : list, optional
        Tick labels for the y-axis.
    yticklabels_fontsize : float or str, optional
        Font size for the y-axis tick labels.
    xrot : float, optional
        Rotation degree of tick labels for the x-axis.
    xha : str, optional
        Horizontal alignment of tick labels for the x-axis.
    xmin : float, optional
        Minimum value for the x-axis.
    xmax : float, optional
        Maximum value for the x-axis.
    ymin : float, optional
        Minimum value for the y-axis.
    ymax : float, optional
        Maximum value for the x-axis.
    xlog : bool, default: False
        Draw the x-axis in log scale.
    ylog : bool, default: False
        Draw the y-axis in log scale.
    show_legend : bool, default: False
        Show the figure legend.
    legend_loc : str, default: 'best'
        Legend location specified as in matplotlib.pyplot.legend.
    legend_ncol : int, default: 1
        Number of columns that the legend has.
    legend_only : bool, default: False
        Clear the figure and display the legend only.
    legend_fontsize : float or str, optional
        Sets the legend font size.
    legend_markerscale : float, optional
        Relative size of legend markers compared with the original.

    Returns
    -------
    matplotlib.axes.Axes
        Returns the Axes object with the plot drawn onto it.

    Notes
    -----
    Font size can be specified by provding a number or a string as defined in: 
    {'xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large'}.
    """
    if isinstance(title, str):
        ax.set_title(title, fontsize=title_fontsize)

    if isinstance(xlabel, str):
        ax.set_xlabel(xlabel, fontsize=xlabel_fontsize)

    if isinstance(ylabel, str):
        ax.set_ylabel(ylabel, fontsize=ylabel_fontsize)

    if isinstance(zlabel, str):
        ax.set_zlabel(zlabel, fontsize=zlabel_fontsize)

    if hide_xtexts:
        ax.set_xlabel('')
        ax.set_xticklabels([])

    if hide_ytexts:
        ax.set_ylabel('')
        ax.set_yticklabels([])

    if hide_ztexts:
        ax.set_zlabel('')
        ax.set_zticklabels([])

    if hide_xlabel:
        ax.set_xlabel('')

    if hide_ylabel:
        ax.set_ylabel('')

    if hide_zlabel:
        ax.set_zlabel('')

    if hide_xticks:
        ax.set_xticks([])

    if hide_yticks:
        ax.set_yticks([])

    if hide_zticks:
        ax.set_zticks([])

    if hide_xticklabels:
        ax.set_xticklabels([])

    if hide_yticklabels:
        ax.set_yticklabels([])

    if isinstance(xticks, list):
        ax.set_xticks(xticks)

    if isinstance(yticks, list):
        ax.set_yticks(yticks)

    if isinstance(xticklabels, list):
        a = len(ax.get_xticklabels())
        b = len(xticklabels)
        if a != b:
            raise ValueError(f"Expected {a} items, but found {b}")
        ax.set_xticklabels(xticklabels)

    if xticklabels_fontsize is not None:
        ax.tick_params(axis='x', which='major', labelsize=xticklabels_fontsize)

    if isinstance(yticklabels, list):
        a = len(ax.get_yticklabels())
        b = len(yticklabels)
        if a != b:
            raise ValueError(f"Expected {a} items, but found {b}")
        ax.set_yticklabels(yticklabels)

    if yticklabels_fontsize is not None:
        ax.tick_params(axis='y', which='major', labelsize=yticklabels_fontsize)

    if isinstance(xrot, numbers.Number):
        ax.set_xticklabels(ax.get_xticklabels(), rotation=xrot)

    if isinstance(xha, str):
        ax.set_xticklabels(ax.get_xticklabels(), ha=xha)

    ax.set_xlim(left=xmin, right=xmax)
    ax.set_ylim(bottom=ymin, top=ymax)

    if xlog:
        ax.set_xscale('log')

    if ylog:
        ax.set_yscale('log')

    # Control the figure legend.
    h, l = ax.get_legend_handles_labels()

    if legend_short:
        l = [_pretty_taxa(x) for x in l]

    if legend_labels:
        a = len(legend_labels)
        b = len(l)
        if a != b:
            m = f"Expected {b} legend labels, received {a}"
            raise ValueError(m)
        l = legend_labels

    if remove_duplicates:
        if h:
            n = int(len(h) / 2)
            h, l = h[:n], l[:n]

    if legend_only:
        ax.clear()
        ax.legend(h, l, loc=legend_loc, ncol=legend_ncol, fontsize=legend_fontsize, markerscale=legend_markerscale)
        ax.axis('off')
    elif show_legend:
        if h:
            ax.legend(h, l, loc=legend_loc, ncol=legend_ncol, fontsize=legend_fontsize, markerscale=legend_markerscale)
        else:
            warnings.warn("No handles with labels found to put in legend.")
    else:
        if ax.get_legend():
            ax.get_legend().remove()
        else:
            pass

    return ax










def _get_others_col(df, count, taxa_names, show_others):
    "Returns DataFrame object after selecting taxa."
    if count is not 0 and taxa_names is not None:
        m = "Cannot use 'count' and 'taxa_names' arguments together"
        raise ValueError(m)
    elif count is not 0:
        if count < df.shape[1]:
            others = df.iloc[:, count-1:].sum(axis=1)
            df = df.iloc[:, :count-1]
            if show_others:
                df = df.assign(Others=others)
        else:
            pass
    elif taxa_names is not None:
        others = df.drop(columns=taxa_names).sum(axis=1)
        df = df[taxa_names]
        if show_others:
            df = df.assign(Others=others)
    else:
        pass

    return df










def _parse_input(input, temp_dir):
    """Parse the input QIIME 2 object and export the files."""
    if isinstance(input, qiime2.Artifact):
        fn = f'{temp_dir}/dokdo-temporary.qza'
        input.save(fn)
        input = fn
        Artifact.load(input).export_data(temp_dir)
    elif isinstance(input, qiime2.Visualization):
        fn = f'{temp_dir}/dokdo-temporary.qzv'
        input.save(fn)
        input = fn
        Visualization.load(input).export_data(temp_dir)
    elif isinstance(input, str) and input.endswith('.qza'):
        Artifact.load(input).export_data(temp_dir)
    elif isinstance(input, str) and input.endswith('.qzv'):
        Visualization.load(input).export_data(temp_dir)
    else:
        pass










# -- General methods ---------------------------------------------------------

def get_mf(metadata):
    """
    This method automatically detects the type of input metadata and converts 
    it to DataFrame object.

    Parameters
    ----------
    metadata : str or qiime2.Metadata
        Metadata file or object.

    Returns
    -------
    pandas.DataFrame
        DataFrame object containing metadata.
    """
    if isinstance(metadata, str):
        mf = Metadata.load(metadata).to_dataframe()
    elif isinstance(metadata, qiime2.Metadata):
        mf = metadata.to_dataframe()
    else:
        raise TypeError(f"Incorrect metadata type: {type(metadata)}")
    return mf










def ordinate(table,
             metadata=None,
             where=None,
             metric='jaccard',
             phylogeny=None):
    """
    This method wraps multiple QIIME 2 methods to perform ordination and 
    returns Artifact object containing PCoA results.

    Under the hood, this method filters the samples (if requested), performs 
    rarefying to the sample with the minimum read depth, computes distance 
    matrix, and then runs PCoA.

    Parameters
    ----------
    table : str
        Table file.
    metadata : str or qiime2.Metadata, optional
        Metadata file or object.
    where : str, optional
        SQLite WHERE clause specifying sample metadata criteria.
    metric : str, default: 'jaccard'
        Metric used for distance matrix computation ('jaccard',
        'bray_curtis', 'unweighted_unifrac', or 'weighted_unifrac').
    phylogeny : str, optional
        Rooted tree file. Required if using 'unweighted_unifrac', or 
        'weighted_unifrac' as metric.

    Returns
    -------
    qiime2.Artifact
        Artifact object containing PCoA results.

    See Also
    --------
    beta_2d_plot
    beta_3d_plot

    Notes
    -----
    The resulting Artifact object can be directly used for plotting by the 
    beta_2d_plot() method.
    """
    if where:
        if metadata is None:
            m = "To use 'where' argument, you must provide metadata"
            raise ValueError(m)
        elif isinstance(metadata, str):
            _metadata = Metadata.load(metadata)
        elif isinstance(metadata, qiime2.Metadata):
            _metadata = metadata
        else:
            raise TypeError(f"Incorrect metadata type: {type(metadata)}")

        filter_result = feature_table.methods.filter_samples(
            table=Artifact.load(table),
            metadata=_metadata,
            where=where,
        )
        _table = filter_result.filtered_table
    else:
        _table = Artifact.load(table)

    min_depth = int(_table.view(pd.DataFrame).sum(axis=1).min())

    rarefy_result = feature_table.methods.rarefy(table=_table,
                                                 sampling_depth=min_depth)
    
    rarefied_table = rarefy_result.rarefied_table

    if metric == 'jaccard':
        distance_matrix_result = diversity_lib.methods.jaccard(table=rarefied_table)
    elif metric == 'bray_curtis':
        distance_matrix_result = diversity_lib.methods.bray_curtis(table=rarefied_table)
    elif metric == 'unweighted_unifrac':
        distance_matrix_result = diversity_lib.methods.unweighted_unifrac(table=rarefied_table, phylogeny=Artifact.load(phylogeny))
    elif metric == 'weighted_unifrac':
        distance_matrix_result = diversity_lib.methods.weighted_unifrac(table=rarefied_table, phylogeny=Artifact.load(phylogeny))
    else:
        raise ValueError(f"Incorrect metric detected: {metric}")
    
    distance_matrix = distance_matrix_result.distance_matrix
    
    pcoa_result = diversity.methods.pcoa(distance_matrix=distance_matrix)

    return pcoa_result.pcoa










# -- Main plotting methods ---------------------------------------------------

def read_quality_plot(demux,
                      strand='forward',
                      ax=None,
                      figsize=None,
                      artist_kwargs=None):
    """
    This method creates a read quality plot.

    Parameters
    ----------
    demux : str or qiime2.Visualization
        Visualization file or object from the q2-demux plugin.
    strand : str, default: 'forward'
        Read strand to be displayed (either 'forward' or 'reverse').
    ax : matplotlib.axes.Axes, optional
        Axes object to draw the plot onto, otherwise uses the current Axes.
    figsize : tuple, optional
        Width, height in inches. Format: (float, float).
    artist_kwargs : dict, optional
        Keyword arguments passed down to the _artist() method.

    Returns
    -------
    matplotlib.axes.Axes
        Returns the Axes object with the plot drawn onto it.

    Notes
    -----
    Example usage of the q2-demux plugin:
        CLI -> $ qiime demux summarize [OPTIONS]
        API -> from qiime2.plugins.demux.visualizers import summarize
    """
    l = ['forward', 'reverse']

    if strand not in l:
        raise ValueError(f"Strand should be one of the following: {l}")

    with tempfile.TemporaryDirectory() as t:
        _parse_input(demux, t)

        df = pd.read_table(f'{t}/{strand}-seven-number-summaries.tsv',
                           index_col=0,
                           skiprows=[1])

    df = pd.melt(df.reset_index(), id_vars=['index'])
    df['variable'] = df['variable'].astype('int64')
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    sns.boxplot(x='variable',
                y='value',
                data=df,
                ax=ax,
                fliersize=0,
                boxprops=dict(color='white', edgecolor='black'),
                medianprops=dict(color='red'),
                whiskerprops=dict(linestyle=':'))

    xticks = np.arange(df['variable'].min(), df['variable'].max(), 20).tolist()

    if artist_kwargs is None:
        artist_kwargs = {}

    artist_kwargs = {'xlabel': 'Sequence base',
                     'ylabel': 'Quality score',
                     'xticks': xticks,
                     'xticklabels': xticks,
                     'ymin': 0,
                     'ymax': 45,
                     **artist_kwargs}

    ax = _artist(ax, **artist_kwargs)

    return ax










def denoising_stats_plot(stats,
                         metadata,
                         where,
                         ax=None,
                         figsize=None,
                         pseudocount=False,
                         order=None,
                         hide_nsizes=False,
                         artist_kwargs=None):
    """
    This method creates a grouped box chart using denoising statistics from 
    the DADA 2 algorithm.

    Parameters
    ----------
    stats : str or qiime2.Artifact
        Artifact file or object from the q2-dada2 plugin.
    metadata : str or qiime2.Metadata
        Metadata file or object.
    where : str
        Column name of the sample metadata.
    ax : matplotlib.axes.Axes, optional
        Axes object to draw the plot onto, otherwise uses the current Axes.
    figsize : tuple, optional
        Width, height in inches. Format: (float, float).
    pseudocount : bool, default: False
        Add pseudocount to remove zeros.
    order : list, optional
        Order to plot the categorical levels in.
    hide_nsizes : bool, default: False
        Hide sample size from x-axis labels.
    artist_kwargs : dict, optional
        Keyword arguments passed down to the _artist() method.

    Returns
    -------
    matplotlib.axes.Axes
        Returns the Axes object with the plot drawn onto it.

    Notes
    -----
    Example usage of the q2-dada2 plugin:
        CLI -> qiime dada2 denoise-paired [OPTIONS]
        API -> from qiime2.plugins.dada2.methods import denoise_paired
    """
    with tempfile.TemporaryDirectory() as t:
        _parse_input(stats, t)

        df1 = pd.read_table(f'{t}/stats.tsv', skiprows=[1], index_col=0)

    mf = get_mf(metadata)

    df2 = pd.concat([df1, mf], axis=1, join='inner')

    a = ['input', 'filtered', 'denoised', 'merged', 'non-chimeric', where]
    df3 = pd.melt(df2[a], id_vars=[where])

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    if pseudocount:
        df3['value'] = df3['value'] + 1

    sns.boxplot(x=where,
                y='value',
                data=df3,
                hue='variable',
                ax=ax,
                order=order)

    if hide_nsizes is False:
        nsizes = df2[where].value_counts().to_dict()
        xtexts = [x.get_text() for x in ax.get_xticklabels()]
        xtexts = [f'{x} ({nsizes[x]})' for x in xtexts]
        ax.set_xticklabels(xtexts)

    if artist_kwargs is None:
        artist_kwargs = {}

    artist_kwargs = {'xlabel': where,
                     'ylabel': 'Read depth',
                     **artist_kwargs}

    ax = _artist(ax, **artist_kwargs)

    return ax










def alpha_rarefaction_plot(rarefaction,
                           hue='sample-id',
                           metric='shannon',
                           ax=None,
                           figsize=None,
                           hue_order=None,
                           artist_kwargs=None):
    """
    This method creates an alpha rarefaction plot.

    Parameters
    ----------
    rarefaction : str or qiime2.Visualization
        Visualization file or object from the q2-diversity plugin.
    hue : str, default: 'sample-id'
        Grouping variable that will produce lines with different colors.
    metric : str, default: 'shannon'
        Diversity metric ('shannon', 'observed_features', or 'faith_pd').
    ax : matplotlib.axes.Axes, optional
        Axes object to draw the plot onto, otherwise uses the current Axes.
    figsize : tuple, optional
        Width, height in inches. Format: (float, float).
    hue_order : list, optional
        Specify the order of categorical levels of the 'hue' semantic.
    artist_kwargs : dict, optional
        Keyword arguments passed down to the _artist() method.

    Returns
    -------
    matplotlib.axes.Axes
        Returns the Axes object with the plot drawn onto it.

    Notes
    -----
    Example usage of the q2-diversity plugin:
        CLI -> qiime diversity alpha-rarefaction [OPTIONS]
        API -> from qiime2.plugins.diversity.visualizers import alpha_rarefaction
    """
    l = ['observed_features', 'faith_pd', 'shannon']

    if metric not in l:
        raise ValueError(f"Metric should be one of the following: {l}")

    with tempfile.TemporaryDirectory() as t:
        _parse_input(rarefaction, t)

        df = pd.read_csv(f'{t}/{metric}.csv', index_col=0)

    metadata_columns = [x for x in df.columns if 'iter' not in x]

    df = pd.melt(df.reset_index(), id_vars=['sample-id'] + metadata_columns)

    df['variable'] = df['variable'].str.split('_').str[0].str.replace(
                         'depth-', '').astype(int)

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    sns.lineplot(x='variable',
                 y='value',
                 data=df,
                 hue=hue,
                 ax=ax,
                 err_style='bars',
                 sort=False,
                 hue_order=hue_order)

    if artist_kwargs is None:
        artist_kwargs = {}

    artist_kwargs = {'xlabel': 'Sequencing depth',
                     'ylabel': metric,
                     **artist_kwargs}

    ax = _artist(ax, **artist_kwargs)

    return ax










def alpha_diversity_plot(significance,
                         where,
                         ax=None,
                         figsize=None,
                         add_swarmplot=False,
                         order=None,
                         artist_kwargs=None):
    """
    This method creates an alpha diversity plot.

    Parameters
    ----------
    significance : str or qiime2.Visualization
        Visualization file or object from the q2-diversity plugin.
    where : str
        Column name to be used for the x-axis.
    ax : matplotlib.axes.Axes, optional
        Axes object to draw the plot onto, otherwise uses the current Axes.
    figsize : tuple, optional
        Width, height in inches. Format: (float, float).
    add_swarmplot : bool, default: False
        Add a swarm plot on top of the box plot.
    order : list, optional
        Order to plot the categorical levels in.
    artist_kwargs : dict, optional
        Keyword arguments passed down to the _artist() method.

    Returns
    -------
    matplotlib.axes.Axes
        Returns the Axes object with the plot drawn onto it.

    Notes
    -----
    Example usage of the q2-diversity plugin:
        CLI -> qiime diversity alpha-group-significance [OPTIONS]
        API -> from qiime2.plugins.diversity.visualizers import alpha_group_significance
    """
    with tempfile.TemporaryDirectory() as t:
        _parse_input(significance, t)

        df = Metadata.load(f'{t}/metadata.tsv').to_dataframe()

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    metric = df.columns[-1]

    boxprops = dict(color='white', edgecolor='black')

    d = {'x': where, 'y': metric, 'ax': ax, 'order': order, 'data': df}

    sns.boxplot(boxprops=boxprops, **d)

    if add_swarmplot:
        sns.swarmplot(**d)

    if artist_kwargs is None:
        artist_kwargs = {}

    artist_kwargs = {'xlabel': where,
                     'ylabel': metric,
                     **artist_kwargs}

    ax = _artist(ax, **artist_kwargs)

    return ax










def beta_2d_plot(ordination,
                 metadata=None,
                 hue=None,
                 size=None,
                 style=None,
                 s=80,
                 alpha=None,
                 ax=None,
                 figsize=None,
                 hue_order=None,
                 style_order=None,
                 legend_type='brief',
                 artist_kwargs=None):
    """
    This method creates a 2D beta diversity plot.

    Parameters
    ----------
    ordination : str or qiime2.Artifact
        Artifact file or object from the q2-diversity plugin.
    metadata : str or qiime2.Metadata, optional
        Metadata file or object.
    hue : str, optional
        Grouping variable that will produce points with different colors.
    size : str, optional
        Grouping variable that will produce points with different sizes.
    style : str, optional
        Grouping variable that will produce points with different markers.
    s : int, default: 80
        Marker size.
    alpha : float, optional
        Proportional opacity of the points.
    ax : matplotlib.axes.Axes, optional
        Axes object to draw the plot onto, otherwise uses the current Axes.
    figsize : tuple, optional
        Width, height in inches. Format: (float, float).
    hue_order : list, optional
        Specify the order of categorical levels of the 'hue' semantic.
    style_order : list, optional
        Specify the order of categorical levels of the 'style' semantic.
    legend_type : str, default: 'brief'
        Legend type as in seaborn.scatterplot ('brief' or 'full').
    artist_kwargs : dict, optional
        Keyword arguments passed down to the _artist() method.

    Returns
    -------
    matplotlib.axes.Axes
        Returns the Axes object with the plot drawn onto it.

    See Also
    --------
    ordinate
    beta_3d_plot

    Notes
    -----
    Example usage of the q2-diversity plugin:
        CLI -> qiime diversity pcoa [OPTIONS]
        API -> from qiime2.plugins.diversity.methods import pcoa
    """
    with tempfile.TemporaryDirectory() as t:
        _parse_input(ordination, t)

        df1 = pd.read_table(f'{t}/ordination.txt', header=None, index_col=0,
                            skiprows=[0, 1, 2, 3, 4, 5, 6, 7, 8],
                            skipfooter=4, engine='python', usecols=[0, 1, 2])

        df1.columns = ['A1', 'A2']

        if metadata is None:
            df2 = df1
        else:
            mf = get_mf(metadata)
            df2 = pd.concat([df1, mf], axis=1, join='inner')

        with open(f'{t}/ordination.txt') as f:
            v = [round(float(x) * 100, 2) for x in f.readlines()[4].split('\t')]

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    sns.scatterplot(data=df2,
                    x='A1',
                    y='A2',
                    hue=hue,
                    hue_order=hue_order,
                    style=style,
                    style_order=style_order,
                    size=size,
                    ax=ax,
                    s=s,
                    alpha=alpha,
                    legend=legend_type)

    if artist_kwargs is None:
        artist_kwargs = {}

    artist_kwargs = {'xlabel': f'Axis 1 ({v[0]} %)',
                     'ylabel': f'Axis 2 ({v[1]} %)',
                     'hide_xticks': True,
                     'hide_yticks': True,
                     **artist_kwargs}

    ax = _artist(ax, **artist_kwargs)

    return ax










def beta_3d_plot(ordination,
                 metadata,
                 hue=None,
                 azim=-60,
                 elev=30,
                 s=80, 
                 ax=None,
                 figsize=None,
                 hue_order=None,
                 artist_kwargs=None):
    """
    This method creates a 3D beta diversity plot.

    Parameters
    ----------
    ordination : str or qiime2.Artifact
        Artifact file or object from the q2-diversity plugin.
    metadata : str or qiime2.Metadata
        Metadata file or object.
    hue : str, optional
        Grouping variable that will produce points with different colors.
    azim : int, default: -60
        Elevation viewing angle.
    elev : int, default: 30
        Azimuthal viewing angle.
    s : int, default: 80
        Marker size.
    ax : matplotlib.axes.Axes, optional
        Axes object to draw the plot onto, otherwise uses the current Axes.
    figsize : tuple, optional
        Width, height in inches. Format: (float, float).
    hue_order : list, optional
        Specify the order of categorical levels of the 'hue' semantic.
    artist_kwargs : dict, optional
        Keyword arguments passed down to the _artist() method.

    Returns
    -------
    matplotlib.axes.Axes
        Returns the Axes object with the plot drawn onto it.

    See Also
    --------
    ordinate
    beta_2d_plot

    Notes
    -----
    Example usage of the q2-diversity plugin:
        CLI -> qiime diversity pcoa [OPTIONS]
        API -> from qiime2.plugins.diversity.methods import pcoa
    """
    with tempfile.TemporaryDirectory() as t:
        _parse_input(ordination, t)

        df = pd.read_table(f'{t}/ordination.txt',
                           header=None,
                           index_col=0,
                           skiprows=[0, 1, 2, 3, 4, 5, 6, 7, 8],
                           skipfooter=4,
                           engine='python')

        df = df.sort_index()

        mf = get_mf(metadata)
        mf = mf.sort_index()
        mf = mf.assign(**{'sample-id': mf.index})

        with open(f'{t}/ordination.txt') as f:
            v = [round(float(x) * 100, 2) for x in f.readlines()[4].split('\t')]

    if ax is None:
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(1, 1, 1, projection='3d')

    ax.view_init(azim=azim, elev=elev)

    d = {'s': s}

    if hue is None:
        ax.scatter(df.iloc[:, 0],
                   df.iloc[:, 1],
                   df.iloc[:, 2],
                   **d)
    else:
        if hue_order is None:
            levels = sorted(mf[hue].unique())
        else:
            levels = hue_order

        for c in levels:
            i = mf[hue] == c
            df2 = df.loc[i]
            ax.scatter(df2.iloc[:, 0],
                       df2.iloc[:, 1],
                       df2.iloc[:, 2],
                       label=c,
                       **d)

    if artist_kwargs is None:
        artist_kwargs = {}

    artist_kwargs = {'xlabel': f'Axis 1 ({v[0]} %)',
                     'ylabel': f'Axis 2 ({v[1]} %)',
                     'zlabel': f'Axis 3 ({v[2]} %)',
                     'hide_xticks': True,
                     'hide_yticks': True,
                     'hide_zticks': True,
                     **artist_kwargs}

    ax = _artist(ax, **artist_kwargs)

    return ax










def distance_matrix_plot(distance_matrix,
                         bins=100,
                         pairs=None,
                         ax=None,
                         figsize=None,
                         artist_kwargs=None):
    """
    This method creates a histogram from a distance matrix.

    Parameters
    ----------
    distance_matrix : str or qiime2.Artifact
        Artifact file or object from the q2-diversity-lib plugin.
    bins : int, optional
        Number of bins to be displayed.
    pairs : list, optional
        List of sample pairs to be shown in red vertical lines.
    ax : matplotlib.axes.Axes, optional
        Axes object to draw the plot onto, otherwise uses the current Axes.
    figsize : tuple, optional
        Width, height in inches. Format: (float, float).
    artist_kwargs : dict, optional
        Keyword arguments passed down to the _artist() method.

    Returns
    -------
    matplotlib.axes.Axes
        Returns the Axes object with the plot drawn onto it.

    Notes
    -----
    Example usage of the q2-diversity-lib plugin:
        CLI -> qiime diversity-lib jaccard [OPTIONS]
        API -> from qiime2.plugins.diversity_lib.methods import jaccard
    """
    with tempfile.TemporaryDirectory() as t:
        _parse_input(distance_matrix, t)
        df = pd.read_table(f'{t}/distance-matrix.tsv', index_col=0)

    dist = sb.stats.distance.DistanceMatrix(df, ids=df.columns)
    cdist = dist.condensed_form()

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    ax.hist(cdist, bins=bins)

    # https://stackoverflow.com/a/36867493/7481899
    def square_to_condensed(i, j, n):
        assert i != j, "no diagonal elements in condensed matrix"
        if i < j:
            i, j = j, i
        return n*j - j*(j+1)//2 + i - 1 - j

    if pairs:
        idx = []

        for pair in pairs:
            i = square_to_condensed(dist.index(pair[0]), dist.index(pair[1]), len(dist.ids))
            idx.append(cdist[i])

        for i in idx:
            ax.axvline(x=i, c='red')

    if artist_kwargs is None:
        artist_kwargs = {}

    artist_kwargs = {'xlabel': 'Distance',
                     'ylabel': 'Frequency',
                     **artist_kwargs}

    ax = _artist(ax, **artist_kwargs)

    return ax










def taxa_abundance_bar_plot(taxa,
                            metadata=None,
                            level=1,
                            by=None,
                            ax=None,
                            figsize=None,
                            width=0.8,
                            count=0,
                            exclude_samples=None,
                            include_samples=None,
                            exclude_taxa=None,
                            sort_by_names=False,
                            colors=None,
                            label_columns=None,
                            orders=None,
                            sample_names=None,
                            csv_file=None,
                            taxa_names=None,
                            sort_by_mean1=True,
                            sort_by_mean2=True,
                            sort_by_mean3=True,
                            show_others=True,
                            artist_kwargs=None):
    """
    This method creates a taxa abundance plot.

    Although the input visualization file should contain medatadata already, 
    you can replace it with new metadata by using the 'metadata' option.

    Parameters
    ----------
    taxa : str or qiime2.Visualization
        Visualization file or object from the q2-taxa plugin.
    metadata : str or qiime2.Metadata, optional
        Metadata file or object.
    level : int, default: 1
        Taxonomic level at which the features should be collapsed.
    by : list, optional
        Column name(s) to be used for sorting the samples. Using 'index' will 
        sort the samples by their name, in addition to other column name(s) 
        that may have been provided. If multiple items are provided, sorting 
        will occur by the order of the items.
    ax : matplotlib.axes.Axes, optional
        Axes object to draw the plot onto, otherwise uses the current Axes.
    figsize : tuple, optional
        Width, height in inches. Format: (float, float).
    width : float, default: 0.8
        The width of the bars.
    count : int, default: 0
        The number of taxa to display. When 0, display all.
    exclude_samples : dict, optional
        Filtering logic used for sample exclusion.
        Format: {'col': ['item', ...], ...}.
    include_samples : dict, optional
        Filtering logic used for sample inclusion.
        Format: {'col': ['item', ...], ...}.
    exclude_taxa : list, optional
        The taxa names to be excluded when matched. Case insenstivie.
    sort_by_names : bool, default: False
        If true, sort the columns (i.e. species) to be displayed by name.
    colors : list, optional
        The bar colors.
    label_columns : list, optional
        The column names to be used as the x-axis labels.
    orders : dict, optional
        Dictionary of {column1: [element1, element2, ...], column2: 
        [element1, element2...], ...} to indicate the order of items. Used to 
        sort the sampels by the user-specified order instead of ordering 
        numerically or alphabetically.
    sample_names : list, optional
        List of sample IDs to be included.
    csv_file : str, optional
        Path of the .csv file to output the dataframe to.
    taxa_names : list, optional
        List of taxa names to be displayed.
    sort_by_mean1 : bool, default: True
        Sort taxa by their mean relative abundance before sample filtration.
    sort_by_mean2 : bool, default: True
        Sort taxa by their mean relative abundance after sample filtration by 
        'include_samples' or 'exclude_samples'.
    sort_by_mean3 : bool, default: True
        Sort taxa by their mean relative abundance after sample filtration by 
        'sample_names'.
    show_others : bool, default: True
        Include the 'Others' category.
    artist_kwargs : dict, optional
        Keyword arguments passed down to the _artist() method.

    Returns
    -------
    matplotlib.axes.Axes
        Returns the Axes object with the plot drawn onto it.

    See Also
    --------
    taxa_abundance_box_plot

    Notes
    -----
    Example usage of the q2-taxa plugin:
        CLI -> qiime taxa barplot [OPTIONS]
        API -> from qiime2.plugins.taxa.visualizers import barplot
    """
    with tempfile.TemporaryDirectory() as t:
        _parse_input(taxa, t)
        df = pd.read_csv(f'{t}/level-{level}.csv', index_col=0)

    # If provided, update the metadata.
    if metadata is None:
        pass
    else:
        mf = get_mf(metadata)
        cols = _get_mf_cols(df)
        df.drop(columns=cols, inplace=True)
        df = pd.concat([df, mf], axis=1, join='inner')

    # If provided, sort the samples by the user-specified order instead of 
    # ordering numerically or alphabetically. To do this, we will first add a 
    # new temporary column filled with the indicies of the user-provided 
    # list. This column will be used for sorting the samples later instead of 
    # the original column. After sorting, the new column will be dropped from 
    # the dataframe and the original column will replace its place.
    if isinstance(orders, dict):
        for k, v in orders.items():
            u = df[k].unique().tolist()

            if set(u) != set(v):
                message = (f"Target values {u} not matched with user-provided "
                           f"values {v} for metadata column `{k}`")
                raise ValueError(message)

            l = [x for x in range(len(v))]
            d = dict(zip(v, l))
            df.rename(columns={k: f'@{k}'}, inplace=True)
            df[k] = df[f'@{k}'].map(d)

    # If provided, sort the samples for display in the x-axis.
    if isinstance(by, list):
        df = df.sort_values(by=by)

    # If sorting was performed by the user-specified order, remove the 
    # temporary columns and then bring back the original column.
    if isinstance(orders, dict):
        for k in orders:
            df.drop(columns=[k], inplace=True)
            df.rename(columns={f'@{k}': k}, inplace=True)

    # If provided, exclude the specified taxa.
    if isinstance(exclude_taxa, list):
        dropped = []
        for tax in exclude_taxa:
            for col in df.columns:
                if tax.lower() in col.lower():
                    dropped.append(col)
        dropped = list(set(dropped))
        df = df.drop(columns=dropped)

    # Remove the metadata columns.
    cols = _get_mf_cols(df)
    mf = df[cols]
    mf = mf.assign(**{'sample-id': mf.index})
    df = df.drop(columns=cols)

    if sort_by_mean1:
        df = _sort_by_mean(df)

    df, mf = _filter_samples(df, mf, exclude_samples, include_samples)

    if sort_by_mean2:
        df = _sort_by_mean(df)

    # If provided, only include the specified samples.
    if isinstance(sample_names, list):
        df = df.loc[sample_names]
        mf = mf.loc[sample_names]

        if sort_by_mean3:
            df = _sort_by_mean(df)


    # Convert counts to proportions.
    df = df.div(df.sum(axis=1), axis=0)

    df = _get_others_col(df, count, taxa_names, show_others)

    if sort_by_names:
        df = df.reindex(sorted(df.columns), axis=1)

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    if isinstance(colors, list):
        c = colors
    else:
        c = plt.cm.get_cmap('Accent').colors

    df = df * 100

    df.plot.bar(stacked=True,
                legend=False,
                ax=ax,
                width=width,
                color=c,
                linewidth=0)

    # If provided, output the dataframe as a .csv file.
    if csv_file is not None:
        df.to_csv(csv_file)

    if label_columns is not None:
        f = lambda row: ' : '.join(row.values.astype(str))
        xticklabels = mf[label_columns].apply(f, axis=1).tolist()
    else:
        xticklabels = None

    if artist_kwargs is None:
        artist_kwargs = {}

    artist_kwargs = {'xlabel': '',
                     'ylabel': 'Relative abundance (%)',
                     'xticklabels': xticklabels,
                     **artist_kwargs}

    ax = _artist(ax, **artist_kwargs)

    return ax










def taxa_abundance_box_plot(taxa,
                            hue=None,
                            hue_order=None,
                            add_datapoints=False,
                            level=1,
                            by=None,
                            ax=None,
                            figsize=None,
                            count=0,
                            exclude_samples=None,
                            include_samples=None,
                            exclude_taxa=None,
                            sort_by_names=False,
                            sample_names=None,
                            csv_file=None,
                            size=5,
                            pseudocount=False,
                            taxa_names=None,
                            brief_xlabels=False,
                            show_means=False,
                            meanprops=None,
                            show_others=True,
                            sort_by_mean=True,
                            artist_kwargs=None):
    """
    This method creates a taxa abundance box plot.

    Parameters
    ----------
    taxa : str or qiime2.Visualization
        Visualization file or object from the q2-taxa plugin.
    hue : str, optional
        Grouping variable that will produce boxes with different colors.
    hue_order : list, optional
        Specify the order of categorical levels of the 'hue' semantic.
    add_datapoints : bool, default: False
        Show datapoints on top of the boxes.
    level : int, default: 1
        Taxonomic level at which the features should be collapsed.
    by : list, optional
        Column name(s) to be used for sorting the samples. Using 'index' will 
        sort the samples by their name, in addition to other column name(s) 
        that may have been provided. If multiple items are provided, sorting 
        will occur by the order of the items.
    ax : matplotlib.axes.Axes, optional
        Axes object to draw the plot onto, otherwise uses the current Axes.
    figsize : tuple, optional
        Width, height in inches. Format: (float, float).
    count : int, default: 0
        The number of taxa to display. When 0, display all.
    exclude_samples : dict, optional
        Filtering logic used for sample exclusion.
        Format: {'col': ['item', ...], ...}.
    include_samples : dict, optional
        Filtering logic used for sample inclusion.
        Format: {'col': ['item', ...], ...}.
    exclude_taxa : list, optional
        The taxa names to be excluded when matched. Case insenstivie.
    sort_by_names : bool, default: False
        If true, sort the columns (i.e. species) to be displayed by name.
    sample_names : list, optional
        List of sample IDs to be included.
    csv_file : str, optional
        Path of the .csv file to output the dataframe to.
    size : float, default: 5.0
        Radius of the markers, in points.
    pseudocount : bool, default: False
        Add pseudocount to remove zeros.
    taxa_names : list, optional
        List of taxa names to be displayed.
    brief_xlabels : bool, default: False
        If true, only display the smallest taxa rank in the x-axis labels.
    show_means : bool, default: False
        Add means to the boxes.
    meanprops : dict, optional
        The meanprops argument as in matplotlib.pyplot.boxplot.
    show_others : bool, default: True
        Include the 'Others' category.
    sort_by_mean : bool, default: True
        Sort taxa by their mean relative abundance after sample filtration.
    artist_kwargs : dict, optional
        Keyword arguments passed down to the _artist() method.

    Returns
    -------
    matplotlib.axes.Axes
        Returns the Axes object with the plot drawn onto it.

    See Also
    --------
    taxa_abundance_bar_plot
    addpairs

    Notes
    -----
    Example usage of the q2-taxa plugin:
        CLI -> qiime taxa barplot [OPTIONS]
        API -> from qiime2.plugins.taxa.visualizers import barplot
    """
    with tempfile.TemporaryDirectory() as t:
        _parse_input(taxa, t)
        df = pd.read_csv(f'{t}/level-{level}.csv', index_col=0)

    # If provided, sort the samples for display in the x-axis.
    if by:
        df = df.sort_values(by=by)

    # If provided, exclude the specified taxa.
    if isinstance(exclude_taxa, list):
        dropped = []
        for tax in exclude_taxa:
            for col in df.columns:
                if tax.lower() in col.lower():
                    dropped.append(col)
        dropped = list(set(dropped))
        df = df.drop(columns=dropped)

    # Remove the metadata columns.
    cols = _get_mf_cols(df)
    mf = df[cols]
    mf = mf.assign(**{'sample-id': mf.index})
    df = df.drop(columns=cols)

    df, mf = _filter_samples(df, mf, exclude_samples, include_samples)

    # If provided, only include the specified samples.
    if isinstance(sample_names, list):
        df = df.loc[sample_names]
        mf = mf.loc[sample_names]

    if sort_by_mean:
        df = _sort_by_mean(df)

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    # Add a pseudocount.
    if pseudocount:
        df = df + 1

    # Convert counts to proportions.
    df = df.div(df.sum(axis=1), axis=0)

    df = _get_others_col(df, count, taxa_names, show_others)

    if sort_by_names:
        df = df.reindex(sorted(df.columns), axis=1)

    _taxa_names = df.columns

    df = df * 100

    if hue is not None:
        df2 = pd.concat([df, mf[hue]], axis=1, join='inner')
        df2 = pd.melt(df2, id_vars=[hue])
    else:
        df2 = pd.melt(df)



    if meanprops:
        _meanprops = meanprops
    else:
        _meanprops={'marker':'x',
                    'markerfacecolor':'white', 
                    'markeredgecolor':'white',
                    'markersize':'10'}

    d = {}

    if show_means:
        d['showmeans'] = True
        d['meanprops'] = _meanprops

    sns.boxplot(x='variable',
                y='value',
                hue=hue,
                hue_order=hue_order,
                data=df2,
                ax=ax,
                **d)

    if add_datapoints:
        remove_duplicates = True
        sns.swarmplot(x='variable',
                      y='value',
                      hue=hue,
                      hue_order=hue_order,
                      data=df2,
                      ax=ax,
                      color='black',
                      size=size,
                      dodge=True)
    else:
        remove_duplicates = False

    # If provided, output the dataframe as a .csv file.
    if csv_file is not None:
        df3 = pd.concat([df, mf], axis=1, join='inner')
        df3.to_csv(csv_file)

    if brief_xlabels:
        xticklabels = [_pretty_taxa(x) for x in ax.get_xticklabels()]
    else:
        xticklabels = None

    if artist_kwargs is None:
        artist_kwargs = {}

    artist_kwargs = {'xrot': 45,
                     'xha': 'right',
                     'xlabel': '',
                     'ylabel': 'Relative abundance (%)',
                     'xticklabels': xticklabels,
                     'remove_duplicates': remove_duplicates,
                     **artist_kwargs}

    ax = _artist(ax, **artist_kwargs)

    return ax










def ancom_volcano_plot(ancom,
                       ax=None,
                       figsize=None,
                       artist_kwargs=None):
    """
    This method creates an ANCOM volcano plot.

    Parameters
    ----------
    ancom : str
        Visualization file or object from the q2-composition plugin.
    ax : matplotlib.axes.Axes, optional
        Axes object to draw the plot onto, otherwise uses the current Axes.
    figsize : tuple, optional
        Width, height in inches. Format: (float, float).
    artist_kwargs : dict, optional
        Keyword arguments passed down to the _artist() method.

    Returns
    -------
    matplotlib.axes.Axes
        Returns the Axes object with the plot drawn onto it.

    Notes
    -----
    Example usage of the q2-composition plugin:
        CLI -> qiime composition ancom [OPTIONS]
        API -> from qiime2.plugins.composition.visualizers import ancom
    """
    with tempfile.TemporaryDirectory() as t:
        _parse_input(ancom, t)
        df = pd.read_table(f'{t}/data.tsv')

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(df.clr, df.W, s=80, c='black', alpha=0.5)

    if artist_kwargs is None:
        artist_kwargs = {}

    artist_kwargs = {'xlabel': 'clr',
                     'ylabel': 'W',
                     **artist_kwargs}

    ax = _artist(ax, **artist_kwargs)

    return ax










# -- Other plotting methods --------------------------------------------------

def addsig(x1,
           x2,
           y,
           t='',
           h=1.0,
           lw=1.0,
           lc='black',
           tc='black',
           ax=None,
           figsize=None,
           fontsize=None):
    """
    This method adds signifiance annotation between two groups in a box plot.

    Parameters
    ----------
    x1 : float
        Position of the first box.
    x2 : float
        Position of the second box.
    y : float
        Bottom position of the drawing.
    t : str, default: ''
        Text.
    h : float, default: 1.0
        Height of the drawing.
    lw : float, default: 1.0
        Line width.
    lc : str, default: 'black'
        Line color.
    tc : str, default: 'black'
        Text color.
    ax : matplotlib.axes.Axes, optional
        Axes object to draw the plot onto, otherwise uses the current Axes.
    figsize : tuple, optional
        Width, height in inches. Format: (float, float).
    fontsize : float, optional
        Sets the fontsize.

    Returns
    -------
    matplotlib.axes.Axes
        Returns the Axes object with the plot drawn onto it.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    ax.plot([x1, x1, x2, x2], [y, y+h, y+h, y], lw=lw, c=lc)
    ax.text((x1+x2)*0.5, y+h, t, ha='center', va='bottom', color=tc, fontsize=fontsize)
    return ax










def addpairs(taxon,
             csv_file,
             subject,
             category,
             group1,
             group2,
             p1=-0.2,
             p2=0.2,
             ax=None,
             figsize=None):
    """
    This method adds lines between two groups in a plot generated by the 
    taxa_abundance_box_plot() method.

    This method also prints the p-value for Wilcoxon signed-rank test.

    Parameters
    ----------
    taxon : str
        Target taxon name.
    csv_file : str
        Path to csv file.
    subject : str
        Column name to indicate pair information.
    category : str
        Column name to be studied.
    group1 : str
        First group in the category column.
    group2 : str
        Second group in the category column.
    p1 : float, default: -0.2
        Start position of the lines.
    p2 : float, default: 0.2
        End position of the lines.
    ax : matplotlib.axes.Axes, optional
        Axes object to draw the plot onto, otherwise uses the current Axes.
    figsize : tuple, optional
        Width, height in inches. Format: (float, float).

    Returns
    -------
    matplotlib.axes.Axes
        Returns the Axes object with the plot drawn onto it.

    See Also
    --------
    taxa_abundance_box_plot
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    df = pd.read_csv(csv_file)
    df = df.sort_values([subject, category])
    g1 = df[df[category] == group1]
    g2 = df[df[category] == group2]

    pvalue = stats.wilcoxon(g1[taxon], g2[taxon])[1]
    print(pvalue)

    y1 = g1[taxon].tolist()
    y2 = g2[taxon].tolist()
    x1 = [p1 for x in y1]
    x2 = [p2 for x in y1]

    for i in range(len(x1)):
        ax.plot([x1[i],x2[i]], [y1[i], y2[i]])

    return ax









