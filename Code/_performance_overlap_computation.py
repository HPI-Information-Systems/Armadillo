import pandas as pd
import numpy as np
from .data_visualization import *
import matplotlib.pyplot as plt
import torch.nn.functional as F

def plot_box_group(df: pd.DataFrame | str, label_list: list, label_y: str='AE', out_pdf: str=None) -> None:
    """Function to compare the overall performances of a list of models with box plots

    Args:
        df (pd.DataFrame): dataframe containing at least one columns for each label in the label list
        label_list (list): list of the columns to plot
        label_y (str, optional): measure on which to compare on. Defaults to 'AE'.
    """
    if isinstance(df, str):
        df = pd.read_csv(df)
    plt.figure(figsize=(8, 6))
    plt.rcParams.update({'font.size': 16})
    try:
        try:
            ax = pd.DataFrame({'Armadillo\nGittables':df['armadillo_gittables_AE'], 'Armadillo\nWikiLast':df['armadillo_wikilast_AE'],'Overlap Set\nSimilarity':df['AE_os_sim'], 'Jaccard\nSimilarity':df['AE_jsim']}).boxplot(showfliers=False, whis=[0, 100], showmeans=True, meanline=True, medianprops=dict(color='black'), boxprops=dict(color='black'), whiskerprops=dict(color='black'))#, fontsize=11)    
        except:
            ax = pd.DataFrame({'Armadillo\nWikiLast':df['armadillo_wikilast_AE'],'Armadillo\nGittables':df['armadillo_gittables_AE'],'Overlap Set\nSimilarity':df['AE_os_sim'], 'Jaccard\nSimilarity':df['AE_jsim']}).boxplot(showfliers=False, whis=[0, 100], showmeans=True, meanline=True, medianprops=dict(color='black'), boxprops=dict(color='black'), whiskerprops=dict(color='black'))#, fontsize=11)    
    except:
        ax = df[label_list].boxplot(showfliers=False, whis=[0, 100], showmeans=True, meanline=True, medianprops=dict(color='black'), boxprops=dict(color='black'), whiskerprops=dict(color='black'))    
    
    means = df[label_list].mean()
    for i, mean in enumerate(means):
        ax.text(i + 1, mean, f'{mean:.3f}', ha='center', va='bottom', color='green')

    plt.xlabel('Approach')
    plt.ylabel(label_y)
    plt.grid(False)
    if isinstance(out_pdf, str):
        plt.savefig(out_pdf, format="pdf", bbox_inches="tight")
    plt.show()

def predict_overlap_compute_AE(unlabelled: str | pd.DataFrame, embedding_dict: str | dict, out_path: str, mode: str='extend_original_dataset') -> pd.DataFrame:
    """Generate a new pd.DataFrame which is suitable to be plotted.

    Args:
        unlabelled (str | pd.DataFrame): path to the testing dataset containing the exact values of overlaps, expected: 'l_id', 'r_id', 'overlap_pred'
        embedding_dict (str | dict): path to the dictionary containing the table embeddings
        out_path (str): path where to save the newly constructed dataframe with labels

    Returns:
        pd.DataFrame: dataframe with attributes'l_id', 'r_id', 'overlap_pred', 'overlap_true', 'AE'
    """
    print('Loading outputs')
    if isinstance(unlabelled, str):
        d1 = pd.read_csv(unlabelled)
    else:
        d1 = unlabelled
    print('Loading embeddings')
    if type(embedding_dict) == str:
        with open(embedding_dict, 'rb') as f:
            em = pickle.load(f)
    l = []
    out = {
        'r_id' : [],
        's_id' : [],
        'overlap_pred' : [],
        'overlap_true' : [],
        'AE' : []
    }
    
    for i in tqdm(range(d1.shape[0])):
        predictions = max(float(0), F.cosine_similarity(em[str(d1.iloc[i]['r_id'])], em[str(d1.iloc[i]['s_id'])], dim=1))
        try:
            predictions = float(predictions.cpu())
        except:
            pass 
        try:
            t = float(d1.iloc[i]['a%'])
        except:
            t = float(d1.iloc[i]['table_overlap'])

        if pd.isnull(t):
            t = 0
        ae = abs(predictions-t)

        l.append(abs(predictions-t))

        out['r_id'].append(d1.iloc[i].iloc[0])
        out['s_id'].append(d1.iloc[i].iloc[1])
        out['overlap_pred'].append(predictions)
        out['overlap_true'].append(t)
        out['AE'].append(ae)
    
    if mode == 'extend_original_dataset':
        df_out = pd.concat([d1, pd.DataFrame({'overlap_armadillo':out['overlap_pred'], 'AE_armadillo':out['AE']})], axis=1)
    else:
        df_out = pd.DataFrame(out)

    df_out.to_csv(out_path, index=False)
    print('Output saved')
    
    return df_out

def show_mae_per_bin(results_path: str | pd.DataFrame, granularity: float=0.1, plot: bool=True, box: bool=False, label_true: str='overlap_true', label_AE: str='AE', out_pdf: str=None) -> None:
    """given a dataframe containing the experiment's results display how the mae varies with respect to the expected error

    Args:
        results_path (str | pd.DataFrame): dataframe containing: 'l_id', 'r_id', 'overlap_pred', 'overlap_true', 'AE'
        granularity (float, optional): granularity of the bins. Defaults to 0.1.
        plot (bool, optional): if True plot the results. Defaults to True.
        box (bool, optional): if True the type of plot is a boxplot. Defaults to False.
    """
    if isinstance(results_path, str):
        data = pd.read_csv(results_path)
    else:
        data = results_path
    d = {}
    box_plot = {}
    for i in range(1, 11, 1):
        i /= 10
        prev = round(i-0.1, 2)
        t = data[data[label_true] >= prev]
        t = t[t[label_true] < i]
        print(f'Bin: {i}        n_samples:{len(t)}      MAE:{np.mean(t[label_AE])}')
        d[f'{prev}_{i}'] = round(np.mean(t[label_AE]),2)
        box_plot[f'{prev}_{i}'] = t[label_AE]
    if plot:
        if box:
            print_box_plot(box_plot, 'Correct Label Range', 'Absolute Error (AE)', out_pdf=out_pdf)
        else:
            plot_dict(d,'Correct Label Range','MAE')

def show_mae_per_bin_text_num(results_path: str | pd.DataFrame, x_label: str, plot: bool=True, box: bool=False, only_text: bool=False, only_num: bool=False) -> None:
    """given a dataframe containing the experiment's results display how the mae varies with respect to the expected error

    Args:
        results_path (str | pd.DataFrame): dataframe containing: 'l_id', 'r_id', 'overlap_pred', 'overlap_true', 'AE'
        granularity (float, optional): granularity of the bins. Defaults to 0.1.
        plot (bool, optional): if True plot the results. Defaults to True.
        box (bool, optional): if True the type of plot is a boxplot. Defaults to False.
    """
    data = pd.read_csv(results_path)
    d = {}
    box_plot = {}
    if only_text:
        data = data[ data['is_text'] == True ]
    if only_num:
        data = data[ data['is_num'] == True ]
    for i in range(1, 11, 1):
        i /= 10
        prev = round(i-0.1, 2)
        t = data[data[x_label] >= prev]
        t = t[t[x_label] < i]
        print(f'Bin: {i}        n_samples:{len(t)}      MAE:{np.mean(t["AE"])}')
        d[f'{prev}_{i}'] = round(np.mean(t['AE']),2)
        box_plot[f'{prev}_{i}'] = t['AE']
    if plot:
        if box:
            print_box_plot(box_plot, f'{x_label} Range', 'Absolute Error (AE)')
        else:
            plot_dict(d, f'{x_label} Range', 'MAE')

def add_table_stats(table_dict: str | dict, dataset: str | pd.DataFrame, outpath: str) -> None:
    print('Loading table_dict')
    if isinstance(table_dict, str):
        with open(table_dict, 'rb') as f:
            table_dict = pickle.load(f)
    print('Loading dataset')
    if isinstance(dataset, str):
        dataset = pd.read_csv(dataset)

    new_cols = {
        'area_r':[],
        'area_s':[],
        'areas_ratio':[],
        'tot_area':[]
    }
    for r in tqdm(range(dataset.shape[0])):
        r_table = table_dict[dataset.iloc[r]['r_id']]
        s_table = table_dict[dataset.iloc[r]['s_id']]
        r_area = r_table.shape[0]*r_table.shape[1]
        s_area = s_table.shape[0]*s_table.shape[1]
        tot_area = r_area + s_area
        areas_ratio = min(r_area, s_area)/max(r_area, s_area)
        new_cols['area_r'].append(r_area)
        new_cols['area_s'].append(s_area)
        new_cols['tot_area'].append(tot_area)
        new_cols['areas_ratio'].append(areas_ratio)
    
    new_cols = pd.DataFrame(new_cols)
    out = pd.concat([dataset, new_cols], axis=1)
    out.to_csv(outpath, index=False)

def prepare_dataset_perc_num_str_nans(labelled_dataset: str | pd.DataFrame, stats_dict: str | dict, out_path: str) -> pd.DataFrame:
    """given a labelled dataset enriches it for data visualization

    Args:
        labelled_dataset (str | pd.DataFrame): labelled dataset with AEs
        stats_dict (str | dict): dictionary containing stats about the tables
        out_path (str): file where to save the generated output

    Returns:
        pd.DataFrame: the enriched dataset
    """
    if isinstance(labelled_dataset, str):
        original = pd.read_csv(labelled_dataset)
    else:
        original = labelled_dataset

    if isinstance(stats_dict, str):
        with open(stats_dict, 'rb') as f:
            stats = pickle.load(f)
    else:
        stats = stats_dict

    new_cols = {
        'perc_num':[],
        'perc_text':[],
        'perc_nans':[],
        'areas_ratio':[],
        'area_to_tokens_ratio':[],
        'total_number_of_tokens':[],
        'is_text':[],
        'is_num':[],
        'has_nan':[],
        'tot_area':[],
        'area_l':[],
        'area_r':[],
        'area_min':[],
        'overlap_area_true':[],
        'overlap_area_pred':[],
        'overlap_area_AE':[],
        'overlap_area_error':[]
        }

    for r in tqdm(range(original.shape[0])):

        tot_num = stats[str(original.iloc[r]['l_id'])]['n_num'] + stats[str(original.iloc[r]['r_id'])]['n_num']
        tot_text = stats[str(original.iloc[r]['l_id'])]['n_text'] + stats[str(original.iloc[r]['r_id'])]['n_text']
        tot_nan = stats[str(original.iloc[r]['l_id'])]['n_nan'] + stats[str(original.iloc[r]['r_id'])]['n_nan']
        tot_area = stats[str(original.iloc[r]['l_id'])]['area'] + stats[str(original.iloc[r]['r_id'])]['area']
        area_l = stats[str(original.iloc[r]['l_id'])]['area']
        area_r = stats[str(original.iloc[r]['r_id'])]['area']
        area_min = min(area_l, area_r)
        overlap_area_true = original.iloc[r]['overlap_true'] * area_min
        overlap_area_pred = original.iloc[r]['overlap_pred'] * area_min
        overlap_area_AE = abs(overlap_area_pred - overlap_area_true)
        overlap_area_error = overlap_area_pred - overlap_area_true

        new_cols['area_l'].append(area_l)
        new_cols['area_r'].append(area_r)
        new_cols['area_min'].append(area_min)
        new_cols['overlap_area_true'].append(overlap_area_true)
        new_cols['overlap_area_pred'].append(overlap_area_pred)
        new_cols['overlap_area_AE'].append(overlap_area_AE)
        new_cols['overlap_area_error'].append(overlap_area_error)
        new_cols['tot_area'].append(tot_area)
        new_cols['perc_num'].append(tot_num / tot_area)
        new_cols['perc_text'].append(tot_text / tot_area)
        new_cols['perc_nans'].append(tot_nan / tot_area)
        new_cols['areas_ratio'].append(min(stats[str(original.iloc[r]['l_id'])]['area'], stats[str(original.iloc[r]['r_id'])]['area'])/max(stats[str(original.iloc[r]['l_id'])]['area'], stats[str(original.iloc[r]['r_id'])]['area']))
        tot_token = stats[str(original.iloc[r]['l_id'])]['n_tokens'] + stats[str(original.iloc[r]['r_id'])]['n_tokens']
        new_cols['total_number_of_tokens'].append(stats[str(original.iloc[r]['l_id'])]['n_tokens'] + stats[str(original.iloc[r]['r_id'])]['n_tokens'])
        new_cols['area_to_tokens_ratio'].append(tot_area / tot_token)

        if (stats[str(original.iloc[r]['l_id'])]['is_text'] == True) and (stats[str(original.iloc[r]['r_id'])]['is_text'] == True):
            new_cols['is_text'].append(True)
        else:
            new_cols['is_text'].append(False)
        
        if (stats[str(original.iloc[r]['l_id'])]['is_num'] == True) and (stats[str(original.iloc[r]['r_id'])]['is_num'] == True):
            new_cols['is_num'].append(True)
        else:
            new_cols['is_num'].append(False)
        
        if (stats[str(original.iloc[r]['l_id'])]['has_nan'] == True) or (stats[str(original.iloc[r]['r_id'])]['has_nan'] == True):
            new_cols['has_nan'].append(True)
        else:
            new_cols['has_nan'].append(False)

    tmp_df = pd.DataFrame(new_cols)

    out_df = pd.concat([original, tmp_df], axis=1)

    out_df.to_csv(out_path, index=False)

    return out_df

def print_box_plot(box_plot: dict, label_x: str=None, label_y: str=None, title: str=None, out_pdf: str=None) -> None:
    df = pd.DataFrame(box_plot)
    plt.figure(figsize=(8, 6))
    df.boxplot(showfliers=False, whis=[0, 100], showmeans=True, meanline=True, medianprops=dict(color='black'), boxprops=dict(color='black'), whiskerprops=dict(color='black'))
    for i, mean_value in enumerate(df.mean()):
        plt.annotate(f"{mean_value:.2f}", xy=(i+1, mean_value), xytext=(i+1, mean_value), color='green', ha='center', va='bottom')

    plt.xlabel(label_x)
    plt.ylabel(label_y)
    plt.grid(False)
    if isinstance(out_pdf, str):
        plt.savefig(out_pdf, format="pdf", bbox_inches="tight")
    plt.show()

def show_mae_per_perc_num(results_path: str | pd.DataFrame, labels_dict: str | dict, param_key: str, plot: bool=True, box: bool=False, only_text: bool=False, only_num: bool=False) -> None:
    data = pd.read_csv(results_path)
    d = {}
    box_plot = {}

    if only_text:
        data = data[ data['is_text'] == True ]
    if only_num:
        data = data[ data['is_num'] == True ]

    for i in range(1, 11, 1):
        i /= 10
        prev = round(i-0.1, 2)
        t = data[data['overlap_true'] >= prev]
        t = t[t['overlap_true'] < i]
        print(f'Bin: {i}        n_samples:{len(t)}      MAE:{np.mean(t["AE"])}')
        d[f'{prev}_{i}'] = round(np.mean(t['AE']),2)
        box_plot[f'{prev}_{i}'] = t['AE']
    if plot:
        if box:
            print_box_plot(box_plot, 'Correct Label Range', 'Absolute Error (AE)')
        else:
            plot_dict(d,'Correct Label Range','MAE')


def show_scatter_t_exec_sloth_arm(results: str | pd.DataFrame, x_label: str='tot_area', logx: bool=True, logy: bool=True, output_pdf: str=None, x_axis: str=None, font_size=15) -> None:
    """visualize embedding generation time on the y axis and table area on the x axis

    Args:
        exp_data_file (str | dict): path to a file containing the data related to a "embed_all_no_paral" test or the dictionary containing the actual data
        logx (bool, opt): if True, the x axis is in logscale. Defaults to True.
        logy (bool, opt): if True, the y axis is in logscale. Defaults to False.
    """
    if isinstance(results, str):
        data = pd.read_csv(results)
    else:
        data = results
    try:
        t_execs_sloth = data['sloth_time']
    except:
        t_execs_sloth = data['total_time']
    t_exec_arm_total = data['armadillo_total_time']

    try:
        t_exec_new_emb_already_comp = data['overlap_computations_repeated_armadillo']
    except:
        t_exec_new_emb_already_comp = data['overlap_computation']

    if x_axis == None:
        x = t_execs_sloth
    else:
        x = data[x_axis]
    plt.figure()
    fig, (ax_scatter, ax_kde) = plt.subplots(2, 1, figsize=(8, 8), 
                                            gridspec_kw={'height_ratios': [3, 1]})
    ax_scatter.scatter(x, x, s=3, c='black', alpha=0.7, edgecolors='black', label='Sloth')
    ax_scatter.scatter(x, t_exec_arm_total, s=3, c='blue', alpha=0.7, edgecolors='blue', label='New Tables')
    ax_scatter.scatter(x, t_exec_new_emb_already_comp, s=3, c='red', alpha=0.7, edgecolors='red', label='Embeddings Already Computed')


    sns.histplot(
        data=x, ax=ax_kde,
        label='KDE',
        fill=True, common_norm=False,
        alpha=.5, linewidth=0, color='grey'
    )
    ax_scatter.set_ylabel('Total Overlap Computation Time (s)',fontsize=font_size)
    
    if logx:
        ax_kde.set_xscale('log')    
        ax_scatter.set_xscale('log')
    if logy:
        ax_scatter.set_yscale('log')
    ax_kde.set_yscale('log')
    ax_scatter.legend()

    ax_kde.set_xlabel('Sloth t_exec (s)',fontsize=font_size)
    ax_kde.set_ylabel('Number Of Samples',fontsize=font_size)
    
    ax_scatter.tick_params(axis='both', which='major', labelsize=font_size)  
    ax_kde.tick_params(axis='both', which='major', labelsize=font_size)  

    ax_scatter.tick_params(axis='both', which='both', labelsize=font_size)
    ax_kde.tick_params(axis='both', which='both', labelsize=font_size)  
    
    ax_scatter.legend(fontsize=font_size)

    plt.tight_layout()
    if isinstance(output_pdf, str):
        plt.savefig(output_pdf, format="pdf", bbox_inches="tight")
    plt.show()

def visualize_area_scatter_plot(stats_file: str | pd.DataFrame, label_x: str='tot_area', label_y: str='AE', logx: bool=True, logy: bool=False, 
                                plot_bisector: bool=False, y_limit_low: int=-4000, y_limit_up: int=4000, limit_y: bool=False, 
                                x_limit_left: int=-4000, x_limit_right: int=4000,limit_x: bool=False, out_pdf: str=None) -> None:
    if isinstance(stats_file, str):
        data = pd.read_csv(stats_file)
    else:
        data = stats_file

    keys = list(data.keys())

    areas = list(data[label_x])
    t_execs = list(data[label_y])

    x = areas
    y = t_execs

    fig, (ax_scatter, ax_kde) = plt.subplots(2, 1, figsize=(8, 8), 
                                            gridspec_kw={'height_ratios': [3, 1]})

    ax_scatter.scatter(x, y, s=3, c='orange', alpha=0.7, edgecolors='black')

    if limit_y:
        ax_scatter.set_ylim(y_limit_low, y_limit_up)
    if limit_x:
        if label_x=='overlap_area_AE'and label_y=='overlap_area_true':
            ax_scatter.set_xlim(x_limit_left, x_limit_right)
            ax_kde.set_xlim(x_limit_left, x_limit_right)
        else:
            ax_scatter.set_xlim(right=x_limit_right)
            ax_kde.set_xlim(right=x_limit_right)
    if label_y == 'overlap_area_error':
        ax_scatter.axline((0, 0), (1, 0), linewidth=1, color='black', ls='--')
    if plot_bisector:
        ax_scatter.axline((0, 0), (1, 1), linewidth=1, color='black', ls='--')
        
    sns.histplot(
        data=x, ax=ax_kde,
        label='KDE',
        fill=True, common_norm=False,
        alpha=.5, linewidth=0, color='grey'
    )

    ax_scatter.set_ylabel(label_y)
    if label_x == 'tot_area':
        ax_kde.set_xlabel('Table Area')
    elif label_x == 'AE':
        ax_kde.set_xlabel('Overlap Ratio AE')
    else:
        ax_kde.set_xlabel(label_x)
    
    if logx:
        ax_kde.set_xscale('log')    
        ax_scatter.set_xscale('log')
    if logy:
        ax_scatter.set_yscale('log')
    ax_kde.set_yscale('log')
    
    ax_kde.set_ylabel('Number Of Samples')

    plt.tight_layout()
    if isinstance(out_pdf, str):
        plt.savefig(out_pdf, format="pdf", bbox_inches="tight")
    plt.show()
