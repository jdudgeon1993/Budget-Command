
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_280292bcf99fb8278d2c1171b5680c9c = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_3491f026199f260863edb2ed8767ae51 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.open_add_account", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "11px", ["letterSpacing"] : "0.08em", ["textTransform"] : "uppercase", ["padding"] : "9px 14px", ["borderRadius"] : "8px", ["border"] : "1px dashed #818cf855", ["color"] : "#818cf8", ["cursor"] : "pointer", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["textAlign"] : "center", ["width"] : "100%", ["&:hover"] : ({ ["background"] : "#818cf80d" }) }),onClick:on_click_3491f026199f260863edb2ed8767ae51},children)
    )
});
