class Plot:


    @staticmethod
    def addBreakMarks(ax, where='top', size=0.015, lw=1.5):
        if where == 'top':
            # Top-left
            ax.plot([0-0.5*size, 0.5*size], [1-0.5*size, 1 + 0.5*size],
                    transform=ax.transAxes, color='k', lw=lw, clip_on=False)
            # Top-right
            ax.plot([1 - 0.5*size, 1+0.5*size], [1-0.5*size, 1 + 0.5*size],
                    transform=ax.transAxes, color='k', lw=lw, clip_on=False)

        elif where == 'bottom':
            # Bottom-left
            ax.plot([0-0.5*size, 0.5*size], [0-0.5*size, 0.5*size],
                    transform=ax.transAxes, color='k', lw=lw, clip_on=False)
            # Bottom-right
            ax.plot([1 - 0.5*size, 1+0.5*size], [0-0.5*size, 0.5*size],
                    transform=ax.transAxes, color='k', lw=lw, clip_on=False)

    @staticmethod
    def plotViolin(ax, data, data_protein, ylabel, xtick_label, label,
                edge_colors, face_colors, y_lower_lim=None, position_label=[-0.1, 1.1]):
    
        def style_violin_parts(vp, color='black', linewidth=1.5, linestyle='-'):
            for part in ['cmedians', 'cbars', 'cmins', 'cmaxes']:
                vp[part].set_color(color)
                vp[part].set_linewidth(linewidth)
                vp[part].set_linestyle(linestyle)

        # Plot violins
        vp = ax.violinplot(data, showmedians=True)
        vp2 = ax.violinplot(data_protein, showmedians=True)

        # Axis setup
        ax.set_xticks(range(1, len(xtick_label) + 1))
        ax.set_xticklabels(xtick_label, multialignment="center")  
        ax.set_xlabel('Products')
        ax.set_ylabel(ylabel)

        # Y-axis limits
        bottom = ax.get_ylim()[0]
        if y_lower_lim is not None:
            bottom = y_lower_lim
        ax.set_ylim(bottom=bottom, top=ax.get_ylim()[1] * 1.05)

        # Add label
        ax.text(*position_label, label, transform=ax.transAxes,
                fontsize=24, fontweight='bold', va='top', ha='left')

        # Style primary violin (data)
        for i, pc in enumerate(vp['bodies']):
            pc.set_facecolor(face_colors[i])
            pc.set_edgecolor(edge_colors[i])
            pc.set_alpha(0.8)
        style_violin_parts(vp, color='black', linewidth=1.5)

        # Style secondary violin (data_protein)
        for pc in vp2["bodies"]:
            pc.set_facecolor("none")
        style_violin_parts(vp2, color='black', linewidth=0.5, linestyle=':')

        return ax.get_ylim()

    @classmethod
    def Violin(cls, grouped_data, impacts, impacts_protein):
        import matplotlib.pyplot as plt

        colors = {"gluten": ['#CD5C5C','#F4A6A6'], 
          "SPI": ['#2E8B57','#90EE90'], 
          "SPC": ['#6A5ACD','#D8BFD8'], 
          "PPI": ['#FF8C00','#FFDAB9'], 
          "PPC": ['#4682B4','#B0E0E6']}
        xtick_labels = []
        edge_colors = []
        face_colors = []

        for key, _ in grouped_data:
            if "protein" not in key:
                split_key = key.split("_")
                if split_key[0] == "gluten":
                    xtick_labels.append(f'WG\n{split_key[1]}')
                else:
                    xtick_labels.append(f'{split_key[0]}\n{split_key[1]}')
                edge_colors.append(colors[split_key[0]][0])
                face_colors.append(colors[split_key[0]][1])

        ylabels = [r"GW [$\mathrm{kg}_{\mathrm{CO}_2\text{-eq}}$/kg]",r"PM-HI [DALY/kg]",r"WS [$\mathrm{m}^{3}\text{-eq}$/kg]",r"LU-BL [PDF/kg]"]

        # Create the figure and subplots
        _, axes = plt.subplots(nrows=5, ncols=1, figsize=(12, 16), dpi=300,gridspec_kw={'height_ratios': [1,1,0.24,0.50,1]})

        labels_violin = ["a)","b)","c)","d)"]

        ylim_bottom = (0, 15)
        ylim_top = (15, max(max(sublist) for sublist in impacts_protein[2]) * 1.08)

        # Plot the violin plots in the first column
        j = 0
        for i, ax in enumerate(axes[:]):
            if i == 2:
                cls.plotViolin(ax, impacts[j],impacts_protein[j],ylabels[j],xtick_labels,labels_violin[j],edge_colors,face_colors,0,position_label=[-0.05,1.352])
                ax.set_ylim((ylim_top))
                ax.set_xticks([])
                ax.set_yticks([15,30,45,60])
                ax.set_xticklabels([])
                ax.set_xlabel("")
                ax.set_ylabel("")
            elif i == 3:
                cls.plotViolin(ax, impacts[j],impacts_protein[j],ylabels[j],xtick_labels,"",edge_colors,face_colors,0)
                ax.set_ylim((ylim_bottom))
                ax.set_ylabel(ylabels[j], y=0.75)
                j += 1
            else:
                cls.plotViolin(ax, impacts[j],impacts_protein[j],ylabels[j],xtick_labels,labels_violin[j],edge_colors,face_colors,0,position_label=[-0.05,1.144])
                j += 1

        # Adjust layout
        plt.tight_layout()

        cls.addBreakMarks(axes[2], where='bottom')
        cls.addBreakMarks(axes[3], where='top')

        pos2_0 = axes[2].get_position().bounds
        pos3_0 = axes[3].get_position().bounds

        axes[2].set_position([pos2_0[0], pos2_0[1] - 0.025, pos2_0[2], pos2_0[3] + 0.025])
        axes[3].set_position([pos3_0[0], pos3_0[1], pos3_0[2], pos3_0[3] + 0.025])

        plt.savefig('Figures/violin_plots_value_chains.png',dpi=450)
        plt.show()

    @staticmethod
    def plotStackedBar(ax, data, ylabel, xlabels, ylim_values, label, legend_col_num, position_label=[-0.1,1.1]):
        import numpy as np
        import matplotlib.pyplot as plt

        group_count = len(data)
        bar_width = 0.8
        cumulative = np.zeros(group_count)
        
        data_index = list(range(data.shape[0]))

        cmap = plt.get_cmap("YlGnBu")
        num_colors = 8
        colors = [cmap(i / (num_colors - 1)) for i in range(num_colors)[::-1]]

        for i, column in enumerate(data.columns):
            ax.bar(data_index, data[column], bottom=cumulative, width=bar_width, label=column, color = colors[i], edgecolor = "black", linewidth = 0.5)
            cumulative += data[column]

        ax.set_xticks(data_index)
        ax.set_xticklabels(xlabels)

        ax.text(position_label[0], position_label[1], label, transform=ax.transAxes,
                fontsize=24, fontweight='bold', va='top', ha='left')

        ax.set_xlabel('Products')
        ax.set_ylabel(ylabel)
        if ylim_values:
            ax.set_ylim(ylim_values)

        handles, labels = ax.get_legend_handles_labels()
        handles = handles[::-1]
        labels = ["Transport", "Protein separation electricity", "Protein separation heat", "Protein separation others", "Defatting", "Milling", "Pre-treatment", "Cultivation"]
        ax.legend(handles, labels, loc="upper right", ncols=legend_col_num, frameon=True)

    @classmethod
    def StackedBar(cls, grouped_data, mean_contribution):
        import matplotlib.pyplot as plt

        xtick_labels = []
        for key, _ in grouped_data:
            if "protein" not in key:
                split_key = key.split("_")
                if split_key[0] == "gluten":
                    xtick_labels.append(f'WG\n{split_key[1]}')
                else:
                    xtick_labels.append(f'{split_key[0]}\n{split_key[1]}')

        ylabels = [r"GW [$\mathrm{kg}_{\mathrm{CO}_2\text{-eq}}$/kg]",r"PM-HI [DALY/kg]",r"WS [$\mathrm{m}^{3}\text{-eq}$/kg]",r"LU-BL [PDF/kg]"]

        # Create the figure and subplots
        fig, axes = plt.subplots(nrows=5, figsize=(12, 16), dpi=300,gridspec_kw={'height_ratios': [1,1,0.24,0.50,1]})

        labels_stacked_bar = ["a)","b)","c)","d)"]

        legend_col_num = [1,2]

        ylim_bottom = (0, 10)
        ylim_top = (25, 30) #max(max(sublist) for sublist in Data_protein[2]) * 1.08

        # Plot the stacked bar plots in the second column
        j = 0
        for i, ax in enumerate(axes):
            if i == 2:
                cls.plotStackedBar(ax, mean_contribution.iloc[:,(j*8):(j*8+8)], ylabels[j], xtick_labels, ylim_top, labels_stacked_bar[j],legend_col_num[1],position_label=[-0.05,1.352])
                ax.set_xticks([])
                ax.set_xticklabels([])
                ax.set_xlabel("")
                ax.set_ylabel("")
                #ax.legend().remove()
            elif i == 3:
                cls.plotStackedBar(ax, mean_contribution.iloc[:,(j*8):(j*8+8)], ylabels[j], xtick_labels, ylim_bottom, "",legend_col_num[1])
                ax.set_ylabel(ylabels[j], y=0.75)
                ax.legend().remove()
                j += 1
            else:
                cls.plotStackedBar(ax, mean_contribution.iloc[:,(j*8):(j*8+8)], ylabels[j], xtick_labels, None, labels_stacked_bar[j], legend_col_num[1], position_label=[-0.05,1.144])
                j += 1

        plt.tight_layout()

        #add_break_marks(axes[2, 0], where='bottom',size=0.015*6.2/3.8)
        cls.addBreakMarks(axes[2], where='bottom')

        #add_break_marks(axes[3, 0], where='top',size=0.015*6.2/3.8)
        cls.addBreakMarks(axes[3], where='top')

        pos2 = axes[2].get_position().bounds
        pos3 = axes[3].get_position().bounds

        axes[2].set_position([pos2[0], pos2[1] - 0.025, pos2[2], pos2[3] + 0.025])
        axes[3].set_position([pos3[0], pos3[1], pos3[2], pos3[3] + 0.025])

        plt.savefig('Figures/Results_CA.png',dpi=450)
        plt.show()
    
    @classmethod
    def SobolIndices(cls,sobol_harmonized,sobol_total):
        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors

        names = ["Wheat Gluten (WG)","Soy protein isolate (SPI)","Soy protein concentrate (SPC)","Pea protein isolate (PPI)","Pea protein concentrate (PPC)"]
        min_summary = []
        max_summary = []
        index_summary = []

        for data_dictionary, name in zip(sobol_harmonized,names):
            input_data_dict = list(data_dictionary.values())

            combined = np.dstack([df.values for df in input_data_dict])

            min_values = np.min(combined, axis=2)
            max_values = np.max(combined, axis=2)
            mean_values = (min_values + max_values) / 2

            min_summary.append([0] * 4)
            max_summary.append([0] * 4)
            index_summary.append(name)

            for i, row in enumerate(max_values):
                if any(x >= 0.05 for x in row):
                    min_summary.append(min_values[i])
                    max_summary.append(max_values[i])
                    index_summary.append(input_data_dict[0].index[i])

            cmap = plt.cm.hot_r
            norm = mcolors.Normalize(vmin=0, vmax=1)

            formatted_ranges = np.array([
                f"{abs(round(min_, 2)):>.2f} - {abs(round(max_, 2)):>.2f}" 
                for min_, max_ in zip(min_values.flatten(), max_values.flatten())
            ]).reshape(min_values.shape)

            columns = ["GW","PM-HI","WS","LU-BL"]
            index = input_data_dict[0].index
            range_df = pd.DataFrame(formatted_ranges, index=index, columns=columns)

            _, ax = plt.subplots(figsize=(7,6),dpi=300)
            ax.axis('tight')
            ax.axis('off')
            table = ax.table(cellText=range_df.values, 
                            colLabels=[f"{c}" for c in range_df.columns], 
                            rowLabels=range_df.index, 
                            loc='center',
                            cellLoc='center')

            for i in range(min_values.shape[0]):
                for j in range(min_values.shape[1]):

                    color = cmap(norm(mean_values[i, j]))
                    transparent_color = (color[0], color[1], color[2], 0.5)
                    table[(i+1, j)].set_facecolor(transparent_color)

            for (i, j) in table._cells:
                table.auto_set_column_width([0,1,2,3])
                table.set_fontsize(10)
                if i == 0 or j == -1:  # This identifies row/column label cells
                    table[(i, j)].set_edgecolor('none')
                else:
                    table[(i, j)].set_linewidth(0.5)

            # Save as an image
            plt.tight_layout()
            if sobol_total:
                plt.savefig(f'Figures/sobol_indices_{name}.png',dpi=450)
            else:
                plt.savefig(f'Figures/sobol_indices_{name}_total.png',dpi=450)
            #plt.show()
        
        return min_summary, max_summary, index_summary

    @classmethod
    def SobolIndicesSummarized(cls, min_summary, max_summary, index_summary, sobol_total):
        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors


        mean_summary = (np.array(min_summary) + np.array(max_summary)) / 2

        cmap = plt.cm.hot_r
        norm = mcolors.Normalize(vmin=0, vmax=1)

        formatted_ranges_summary = np.array([
                f"{abs(round(min_, 2)):>.2f} - {abs(round(max_, 2)):>.2f}" 
                for min_, max_ in zip(np.array(min_summary).flatten(), np.array(max_summary).flatten())
            ]).reshape(np.array(min_summary).shape)
        mask = np.all(formatted_ranges_summary == "0.00 - 0.00", axis = 1)
        formatted_ranges_summary[mask] = ""

        columns = ["GW","PM-HI","WS","LU-BL"]
        range_df = pd.DataFrame(formatted_ranges_summary, index=index_summary, columns=columns)

        empty_rows = np.where(np.all(formatted_ranges_summary == "", axis=1))[0]

        fig, ax = plt.subplots(figsize=(6,6),dpi=300)
        ax.axis('tight')
        ax.axis('off')
        table = ax.table(cellText=range_df.values, 
                        colLabels=[f"{c}" for c in range_df.columns], 
                        rowLabels=range_df.index, 
                        loc='center',
                        cellLoc='center')

        for i in range(np.array(min_summary).shape[0]):
            for j in range(np.array(min_summary).shape[1]):

                color = cmap(norm(mean_summary[i, j]))
                transparent_color = (color[0], color[1], color[2], 0.5)
                table[(i+1, j)].set_facecolor(transparent_color)

        for (i, j) in table._cells:
            table.auto_set_column_width([0,1,2,3])
            table.set_fontsize(8)
            if i-1 in empty_rows or i == 0 or j == -1:  # This identifies row/column label cells
                table[(i, j)].set_edgecolor('none')
            else:
                table[(i, j)].set_linewidth(0.5)
            if i == 0 or j == -1 and i-1 in empty_rows:
                table[(i, j)].get_text().set_fontweight("bold")
        # Save as an image
        plt.tight_layout()
        if sobol_total:
            plt.savefig(f'Figures/sobol_indices_summary.png',dpi=450)
        else:
            plt.savefig(f'Figures/sobol_indices_summary_total.png',dpi=450)
        #plt.show()