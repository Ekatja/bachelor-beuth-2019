
import json

from branca.element import Figure, JavascriptLink

from folium.features import GeoJson

from jinja2 import Template


class CustomTimeSliderChoropleth(GeoJson):
    """
    Creates a TimeSliderChoropleth plugin to append into a map with Map.add_child.
    Parameters
    ----------
    data: str
        geojson string
    styledict: dict
        A dictionary where the keys are the geojson feature ids and the values are
        dicts of `{time: style_options_dict}`
    name : string, default None
        The name of the Layer, as it will appear in LayerControls.
    overlay : bool, default False
        Adds the layer as an optional overlay (True) or the base layer (False).
    control : bool, default True
        Whether the Layer will be included in LayerControls.
    show: bool, default True
        Whether the layer will be shown on opening (only for overlays).
    """
    _template = Template(u"""
            {% macro script(this, kwargs) %}
            document.addEventListener("DOMContentLoaded", function(event) {
                var timestamps = {{ this.timestamps }};
                var styledict = {{ this.styledict }};
                var current_timestamp = timestamps[0];
                // insert time slider
                
                d3.select("#year-slider-students").insert("p", ":first-child").append("input")
                    .attr("type", "range")
                    //.attr("width", "100px")
                    .attr("min", 0)
                    .attr("max", timestamps.length - 1)
                    .attr("value", 0)
                    .attr("id", "slider")
                    .attr("step", "1")
                    .style('align', 'center');
                // insert time slider output BEFORE time slider (text on top of slider)
                d3.select("#year-slider-students").insert("p", ":first-child").append("output")
                    .attr("width", "100")
                    .attr("id", "slider-value")
                    .style('font-size', '18px')
                    .style('text-align', 'center')
                    .style('font-weight', '500%');
                var datestring = current_timestamp.toString();
                d3.select("output#slider-value").text(datestring);
                fill_map = function(){
                    for (var feature_id in styledict){
                        let style = styledict[feature_id]//[current_timestamp];
                        var fillColor = 'white';
                        var opacity = 0;
                        if (current_timestamp in style){
                            fillColor = style[current_timestamp]['color'];
                            opacity = style[current_timestamp]['opacity'];
                            d3.selectAll('#feature-'+feature_id
                            ).attr('fill', fillColor)
                            .style('fill-opacity', opacity);
                        }
                    }
                }
                d3.select("#slider").on("input", function() {
                    current_timestamp = timestamps[this.value];
                var datestring = current_timestamp.toString();
                d3.select("output#slider-value").text(datestring);
                fill_map();
                });
                {% if this.highlight %}
                    {{this.get_name()}}_onEachFeature = function onEachFeature(feature, layer) {
                        layer.on({
                            mouseout: function(e) {
                            if (current_timestamp in styledict[e.target.feature.id]){
                                var opacity = styledict[e.target.feature.id][current_timestamp]['opacity'];
                                d3.selectAll('#feature-'+e.target.feature.id).style('fill-opacity', opacity);
                            }
                        },
                            mouseover: function(e) {
                            if (current_timestamp in styledict[e.target.feature.id]){
                                d3.selectAll('#feature-'+e.target.feature.id).style('fill-opacity', 1);
                            }
                        },
                            click: function(e) {
                                {{this._parent.get_name()}}.fitBounds(e.target.getBounds());
                        }
                        });
                    };
                {% endif %}
                var {{this.get_name()}} = L.geoJson(
                    {% if this.embed %}{{this.style_data()}}{% else %}"{{this.data}}"{% endif %}
                    {% if this.smooth_factor is not none or this.highlight %}
                        , {
                        {% if this.smooth_factor is not none  %}
                            smoothFactor:{{this.smooth_factor}}
                        {% endif %}
                        {% if this.highlight %}
                            {% if this.smooth_factor is not none  %}
                            ,
                            {% endif %}
                            onEachFeature: {{this.get_name()}}_onEachFeature
                        {% endif %}
                        }
                    {% endif %}
                    ).addTo({{this._parent.get_name()}}
                );
            {{this.get_name()}}.setStyle(function(feature) {feature.properties.style;});
                {{ this.get_name() }}.eachLayer(function (layer) {
                    layer._path.id = 'feature-' + layer.feature.id;
                    });
                d3.selectAll('path')
                .attr('stroke', 'white')
                .attr('stroke-width', 0.8)
                //.attr('stroke-dasharray', '5,5')
                .attr('fill-opacity', 0);
                fill_map();
                });
            {% endmacro %}
            """)

    def __init__(self, data, styledict, name=None, overlay=True, control=True,
                 show=True):
        super(CustomTimeSliderChoropleth, self).__init__(data, name=name,
                                                   overlay=overlay,
                                                   control=control, show=show)
        if not isinstance(styledict, dict):
            raise ValueError('styledict must be a dictionary, got {!r}'.format(styledict))  # noqa
        for val in styledict.values():
            if not isinstance(val, dict):
                raise ValueError('Each item in styledict must be a dictionary, got {!r}'.format(val))  # noqa

        # Make set of timestamps.
        timestamps = set()
        for feature in styledict.values():
            timestamps.update(set(feature.keys()))
        timestamps = sorted(list(timestamps))

        self.timestamps = json.dumps(timestamps)
        self.styledict = json.dumps(styledict, sort_keys=True, indent=2)

    def render(self, **kwargs):
        super(CustomTimeSliderChoropleth, self).render(**kwargs)
        figure = self.get_root()
        assert isinstance(figure, Figure), ('You cannot render this Element '
                                            'if it is not in a Figure.')
        figure.header.add_child(JavascriptLink('https://d3js.org/d3.v4.min.js'), name='d3v4')
